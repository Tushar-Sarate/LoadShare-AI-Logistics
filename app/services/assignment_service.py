from sqlalchemy.orm import Session

from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order, OrderStatus
from app.services.geo_service import haversine_km, MAX_ASSIGN_KM
from app.services.live_location import get_location

# A live GPS position older than this is ignored (seconds)
GPS_FRESH_SECONDS = 300


def assign_partner(db: Session, order: Order):
    """Assign the NEAREST available partner within MAX_ASSIGN_KM.

    A partner who shares live GPS is measured from the real position.
    Everyone else is measured from the position estimated from their pincode.

    Returns (partner, distance_km) or None.
    Rows are locked (skip_locked) so two orders cannot grab the same partner.
    """

    partners = (
        db.query(DeliveryPartner)
        .filter(DeliveryPartner.is_available == True)  # noqa: E712
        .with_for_update(skip_locked=True)
        .all()
    )

    if order.pickup_lat is None or order.pickup_lng is None:
        return None

    best = None
    best_km = None

    for p in partners:

        live = get_location(p.id, max_age=GPS_FRESH_SECONDS)

        if live:
            lat, lng = live["lat"], live["lng"]
        else:
            lat, lng = p.latitude, p.longitude

        if lat is None or lng is None:
            continue

        km = haversine_km(order.pickup_lat, order.pickup_lng, lat, lng)

        if km <= MAX_ASSIGN_KM and (best_km is None or km < best_km):
            best, best_km = p, km

    if best is None:
        return None

    order.delivery_partner_id = best.id
    order.order_status = OrderStatus.assigned
    best.is_available = False

    return best, best_km