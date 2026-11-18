from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

from app.database import get_db
from app.models.customer import Customer
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order, OrderStatus, PaymentStatus
from app.security.dependencies import get_current_user

from app.schemas.order_schema import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate
)

from app.services.order_service import calculate_charge, ALLOWED_TRANSITIONS
from app.services.assignment_service import assign_partner, GPS_FRESH_SECONDS
from app.services.tracking_service import add_tracking
from app.services.geo_service import coords_for, haversine_km, MAX_ASSIGN_KM
from app.services.eta_service import predict_eta
from app.services.live_location import get_location
from app.services.realtime import notify_order


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


def get_order_or_404(db: Session, order_id: int) -> Order:

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


def check_access(db: Session, user, order: Order):

    if user.role == "admin":
        return

    if user.role == "customer":
        customer = db.query(Customer).filter(
            Customer.user_id == user.id
        ).first()
        if customer and order.customer_id == customer.id:
            return

    if user.role == "delivery_partner":
        partner = db.query(DeliveryPartner).filter(
            DeliveryPartner.user_id == user.id
        ).first()
        if partner and order.delivery_partner_id == partner.id:
            return

    raise HTTPException(
        status_code=403,
        detail="Not allowed to access this order"
    )


def _partner_for(db: Session, user, lock: bool = False) -> DeliveryPartner:

    if user.role != "delivery_partner":
        raise HTTPException(
            status_code=403,
            detail="Only delivery partners can do this"
        )

    query = db.query(DeliveryPartner).filter(
        DeliveryPartner.user_id == user.id
    )

    if lock:
        query = query.with_for_update()

    partner = query.first()

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Partner profile not found"
        )

    return partner


def _partner_position(partner: DeliveryPartner):
    """Real GPS if the partner shares it, otherwise the pincode estimate."""

    live = get_location(partner.id, max_age=GPS_FRESH_SECONDS)

    if live:
        return live["lat"], live["lng"]

    return partner.latitude, partner.longitude


# Create Order (parcel)
@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if current_user.role != "customer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can create orders"
        )

    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    p_lat, p_lng = coords_for(customer.city, order_data.pickup_pincode)
    d_lat, d_lng = coords_for(customer.city, order_data.delivery_pincode)
    km = round(haversine_km(p_lat, p_lng, d_lat, d_lng), 2)

    new_order = Order(
        order_number=f"LS-{uuid4().hex[:10].upper()}",
        customer_id=customer.id,
        pickup_address=order_data.pickup_address,
        pickup_pincode=order_data.pickup_pincode,
        pickup_lat=p_lat,
        pickup_lng=p_lng,
        delivery_address=order_data.delivery_address,
        delivery_pincode=order_data.delivery_pincode,
        delivery_lat=d_lat,
        delivery_lng=d_lng,
        distance_km=Decimal(str(km)),
        eta_minutes=predict_eta(km, 0),
        package_description=order_data.package_description,
        weight_kg=order_data.weight_kg,
        delivery_charge=calculate_charge(order_data.weight_kg, km)
    )

    db.add(new_order)
    db.flush()

    add_tracking(
        db, new_order, OrderStatus.pending,
        current_user.id, "Order placed"
    )

    db.commit()
    db.refresh(new_order)

    notify_order(new_order, "order_new")

    return new_order


# List Orders (each role sees only its own)
@router.get(
    "/",
    response_model=List[OrderResponse]
)
def list_orders(
    order_status: Optional[OrderStatus] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    query = db.query(Order)

    if current_user.role == "customer":
        customer = db.query(Customer).filter(
            Customer.user_id == current_user.id
        ).first()
        if not customer:
            return []
        query = query.filter(Order.customer_id == customer.id)

    elif current_user.role == "delivery_partner":
        partner = db.query(DeliveryPartner).filter(
            DeliveryPartner.user_id == current_user.id
        ).first()
        if not partner:
            return []
        query = query.filter(Order.delivery_partner_id == partner.id)

    if order_status:
        query = query.filter(Order.order_status == order_status)

    return query.order_by(
        Order.created_at.desc()
    ).offset(skip).limit(limit).all()


# Pending orders near the partner, best paying first
# (this route must stay above /{order_id})
@router.get("/available")
def available_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    partner = _partner_for(db, current_user)

    if not partner.is_available:
        return []

    lat, lng = _partner_position(partner)

    if lat is None or lng is None:
        return []

    pending = db.query(Order).filter(
        Order.order_status == OrderStatus.pending
    ).order_by(Order.created_at.desc()).limit(200).all()

    rows = []

    for o in pending:

        if o.pickup_lat is None or o.pickup_lng is None:
            continue

        pickup_km = haversine_km(lat, lng, o.pickup_lat, o.pickup_lng)

        if pickup_km > MAX_ASSIGN_KM:
            continue

        rows.append({
            "id": o.id,
            "order_number": o.order_number,
            "restaurant_name": o.restaurant_name,
            "pickup_address": o.pickup_address,
            "delivery_address": o.delivery_address,
            "pickup_km": round(pickup_km, 1),
            "trip_km": float(o.distance_km or 0),
            "eta_minutes": o.eta_minutes,
            "earn": float(o.delivery_charge),
            "order_value": float(o.delivery_charge) + float(o.items_total or 0),
            "payment_method": o.payment_method,
        })

    rows.sort(key=lambda r: -r["earn"])

    return rows


# Get One Order
@router.get(
    "/{order_id}",
    response_model=OrderResponse
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    order = get_order_or_404(db, order_id)
    check_access(db, current_user, order)

    return order


# A partner accepts a pending order
@router.post(
    "/{order_id}/accept",
    response_model=OrderResponse
)
def accept_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    partner = _partner_for(db, current_user, lock=True)

    # lock the order row so two partners cannot take the same order
    order = db.query(Order).filter(
        Order.id == order_id
    ).with_for_update().first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.order_status != OrderStatus.pending:
        raise HTTPException(
            status_code=400,
            detail="This order was already taken"
        )

    if not partner.is_available:
        raise HTTPException(
            status_code=400,
            detail="Finish your current delivery first"
        )

    lat, lng = _partner_position(partner)

    if lat is None or order.pickup_lat is None:
        raise HTTPException(
            status_code=400,
            detail="Your location is not known yet"
        )

    pickup_km = haversine_km(lat, lng, order.pickup_lat, order.pickup_lng)

    if pickup_km > MAX_ASSIGN_KM:
        raise HTTPException(
            status_code=400,
            detail=f"The pickup is {pickup_km:.0f} km away. The limit is {MAX_ASSIGN_KM:.0f} km."
        )

    order.delivery_partner_id = partner.id
    order.order_status = OrderStatus.assigned
    partner.is_available = False

    add_tracking(
        db, order, OrderStatus.assigned,
        current_user.id,
        f"Accepted by the delivery partner ({pickup_km:.1f} km from pickup)"
    )

    db.commit()
    db.refresh(order)

    notify_order(order)

    return order


# Assign the nearest partner (admin only)
@router.post(
    "/{order_id}/assign",
    response_model=OrderResponse
)
def assign_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    order = get_order_or_404(db, order_id)

    if order.order_status != OrderStatus.pending:
        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be assigned"
        )

    result = assign_partner(db, order)

    if not result:
        raise HTTPException(
            status_code=409,
            detail="No delivery partner available nearby"
        )

    partner, km = result

    add_tracking(
        db, order, OrderStatus.assigned,
        current_user.id, f"Partner assigned ({km:.1f} km from pickup)"
    )

    db.commit()
    db.refresh(order)

    notify_order(order)

    return order


# Update Status
@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse
)
def update_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    order = get_order_or_404(db, order_id)
    check_access(db, current_user, order)

    new_status = data.order_status

    if new_status not in ALLOWED_TRANSITIONS[order.order_status]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot change status from "
                f"{order.order_status.value} to {new_status.value}"
            )
        )

    if current_user.role == "customer":
        if new_status != OrderStatus.cancelled or order.order_status != OrderStatus.pending:
            raise HTTPException(
                status_code=403,
                detail="Customers can only cancel pending orders"
            )

    if current_user.role == "delivery_partner" and new_status not in {
        OrderStatus.picked_up,
        OrderStatus.in_transit,
        OrderStatus.delivered
    }:
        raise HTTPException(
            status_code=403,
            detail="Partners cannot set this status"
        )

    # Cash on delivery: the partner must collect the cash first
    if (
        new_status == OrderStatus.delivered
        and order.payment_method == "COD"
        and order.payment_status != PaymentStatus.paid
    ):
        raise HTTPException(
            status_code=400,
            detail="Collect the cash from the customer first"
        )

    order.order_status = new_status

    add_tracking(db, order, new_status, current_user.id)

    # Free the partner when the job ends
    if new_status in {OrderStatus.delivered, OrderStatus.cancelled} \
            and order.delivery_partner:
        order.delivery_partner.is_available = True

    db.commit()
    db.refresh(order)

    notify_order(order)

    return order