from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.config import UPI_ID, UPI_NAME
from app.database import get_db
from app.models.user import User
from app.models.customer import Customer
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import Payment

from app.schemas.payment_schema import (
    PaymentCreate,
    PaymentResponse
)

from app.services.realtime import notify_order

from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


# UPI details for the QR code
@router.get("/upi-info")
def upi_info(current_user: User = Depends(get_current_user)):

    return {"upi_id": UPI_ID, "name": UPI_NAME}


# Make Payment (customer)
@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED
)
def make_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "customer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can make payments"
        )

    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    order = db.query(Order).filter(
        Order.id == data.order_id,
        Order.customer_id == customer.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.order_status == OrderStatus.cancelled:
        raise HTTPException(
            status_code=400,
            detail="Cannot pay for a cancelled order"
        )

    if order.payment_status == PaymentStatus.paid:
        raise HTTPException(
            status_code=400,
            detail="Order already paid"
        )

    amount = order.delivery_charge + order.items_total

    if data.method == "COD":

        if order.payment_method == "COD":
            raise HTTPException(
                status_code=400,
                detail="Already set to cash on delivery"
            )

        payment = Payment(
            order_id=order.id,
            amount=amount,
            method="COD",
            status=PaymentStatus.pending
        )

        order.payment_method = "COD"

    else:

        if not data.reference:
            raise HTTPException(
                status_code=400,
                detail="Enter the 12-digit UPI reference (UTR) number"
            )

        payment = Payment(
            order_id=order.id,
            amount=amount,
            method="UPI",
            reference=data.reference,
            status=PaymentStatus.paid
        )

        order.payment_method = "UPI"
        order.payment_status = PaymentStatus.paid

    db.add(payment)
    db.commit()
    db.refresh(payment)

    notify_order(order)

    return payment


# Partner confirms cash collected (cash on delivery)
@router.post(
    "/{order_id}/collect-cash",
    response_model=PaymentResponse
)
def collect_cash(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "delivery_partner":
        raise HTTPException(
            status_code=403,
            detail="Only the delivery partner can collect cash"
        )

    partner = db.query(DeliveryPartner).filter(
        DeliveryPartner.user_id == current_user.id
    ).first()

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order or not partner or order.delivery_partner_id != partner.id:
        raise HTTPException(
            status_code=403,
            detail="This order is not assigned to you"
        )

    if order.payment_method != "COD":
        raise HTTPException(
            status_code=400,
            detail="This order is not cash on delivery"
        )

    if order.payment_status == PaymentStatus.paid:
        raise HTTPException(
            status_code=400,
            detail="Cash already collected"
        )

    if order.order_status != OrderStatus.in_transit:
        raise HTTPException(
            status_code=400,
            detail="Collect cash when the order is out for delivery"
        )

    payment = db.query(Payment).filter(
        Payment.order_id == order.id,
        Payment.method == "COD",
        Payment.status == PaymentStatus.pending
    ).order_by(Payment.id.desc()).first()

    if payment:
        payment.status = PaymentStatus.paid
    else:
        payment = Payment(
            order_id=order.id,
            amount=order.delivery_charge + order.items_total,
            method="COD",
            status=PaymentStatus.paid
        )
        db.add(payment)

    order.payment_status = PaymentStatus.paid

    db.commit()
    db.refresh(payment)

    notify_order(order)

    return payment


# Get Payments of an Order
@router.get(
    "/order/{order_id}",
    response_model=List[PaymentResponse]
)
def get_order_payments(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if current_user.role == "customer":

        customer = db.query(Customer).filter(
            Customer.user_id == current_user.id
        ).first()

        if not customer or order.customer_id != customer.id:
            raise HTTPException(
                status_code=403,
                detail="Not allowed to view these payments"
            )

    elif current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not allowed to view these payments"
        )

    return db.query(Payment).filter(
        Payment.order_id == order_id
    ).all()