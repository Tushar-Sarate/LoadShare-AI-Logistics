from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.customer import Customer
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order
from app.models.tracking import Tracking

from app.schemas.tracking_schema import TrackingResponse

from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/tracking",
    tags=["Tracking"]
)


# Get Order Tracking History
@router.get(
    "/{order_id}",
    response_model=List[TrackingResponse]
)
def get_order_tracking(
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
                detail="Not allowed to view this order"
            )

    elif current_user.role == "delivery_partner":

        partner = db.query(DeliveryPartner).filter(
            DeliveryPartner.user_id == current_user.id
        ).first()

        if not partner or order.delivery_partner_id != partner.id:
            raise HTTPException(
                status_code=403,
                detail="Not allowed to view this order"
            )

    return db.query(Tracking).filter(
        Tracking.order_id == order_id
    ).order_by(Tracking.created_at).all()