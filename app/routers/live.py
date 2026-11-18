from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order, OrderStatus
from app.routers.orders import check_access, get_order_or_404
from app.security.dependencies import get_current_user
from app.services.geo_service import haversine_km
from app.services.live_location import set_location, get_location
from app.services.realtime import publish


router = APIRouter(
    prefix="/live",
    tags=["Live tracking"]
)

ACTIVE = (
    OrderStatus.assigned,
    OrderStatus.picked_up,
    OrderStatus.in_transit
)


class LocationUpdate(BaseModel):

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    accuracy: Optional[float] = Field(default=None, ge=0)
    simulated: bool = False


def _km_to_drop(order: Order, lat: float, lng: float):

    if order.delivery_lat is None or order.delivery_lng is None:
        return None

    return round(haversine_km(lat, lng, order.delivery_lat, order.delivery_lng), 2)


# Partner sends the current position
@router.post("/location")
def update_location(
    data: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "delivery_partner":
        raise HTTPException(
            status_code=403,
            detail="Only delivery partners can share a location"
        )

    partner = db.query(DeliveryPartner).filter(
        DeliveryPartner.user_id == current_user.id
    ).first()

    if not partner:
        raise HTTPException(status_code=404, detail="Partner profile not found")

    set_location(partner.id, data.lat, data.lng, data.accuracy, data.simulated)

    orders = db.query(Order).filter(
        Order.delivery_partner_id == partner.id,
        Order.order_status.in_(ACTIVE)
    ).all()

    # push the position to each customer and to the admins
    for o in orders:

        user_ids = set()
        if o.customer is not None:
            user_ids.add(o.customer.user_id)

        publish(user_ids, {"admin"}, {
            "type": "location",
            "order_id": o.id,
            "lat": data.lat,
            "lng": data.lng,
            "km_to_drop": _km_to_drop(o, data.lat, data.lng),
            "simulated": data.simulated,
        })

    return {"ok": True, "orders": len(orders)}


# Current position of the partner delivering this order
@router.get("/order/{order_id}")
def order_location(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    order = get_order_or_404(db, order_id)
    check_access(db, current_user, order)

    active = order.order_status in ACTIVE
    location = None

    # the position is only shared while the order is on the way
    if active and order.delivery_partner_id:

        loc = get_location(order.delivery_partner_id, max_age=600)

        if loc:
            location = {
                "lat": loc["lat"],
                "lng": loc["lng"],
                "age_seconds": loc["age_seconds"],
                "simulated": loc["simulated"],
                "km_to_drop": _km_to_drop(order, loc["lat"], loc["lng"]),
            }

    return {
        "order_id": order.id,
        "status": order.order_status.value,
        "partner_assigned": order.delivery_partner_id is not None,
        "location": location,
    }