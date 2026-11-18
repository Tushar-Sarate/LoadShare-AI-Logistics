from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from decimal import Decimal
from uuid import uuid4

from app.database import get_db
from app.models.user import User
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.restaurant import Restaurant, MenuItem

from app.schemas.order_schema import OrderResponse
from app.schemas.restaurant_schema import FoodOrderCreate

from app.services.tracking_service import add_tracking
from app.services.order_service import food_delivery_fee
from app.services.geo_service import coords_for, haversine_km, MAX_DELIVERY_KM
from app.services.eta_service import predict_eta
from app.services.realtime import notify_order

from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/food-orders",
    tags=["Food Orders"]
)


def _get_customer(db: Session, user: User) -> Customer:

    if user.role != "customer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can order food"
        )

    customer = db.query(Customer).filter(
        Customer.user_id == user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    return customer


def _get_restaurant(db: Session, restaurant_id: int) -> Restaurant:

    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    return restaurant


def _trip(restaurant: Restaurant, customer: Customer, pincode: str):
    """Coordinates of both ends and the distance in km (2 decimals)."""

    r_lat, r_lng = restaurant.latitude, restaurant.longitude
    if r_lat is None or r_lng is None:
        r_lat, r_lng = coords_for(restaurant.city, restaurant.pincode)

    d_lat, d_lng = coords_for(customer.city, pincode)
    km = round(haversine_km(r_lat, r_lng, d_lat, d_lng), 2)

    return r_lat, r_lng, d_lat, d_lng, km


# Price quote shown in the cart (distance, fee, arrival time)
@router.get("/quote")
def quote(
    restaurant_id: int,
    delivery_pincode: str = Query(pattern=r"^\d{6}$"),
    items: int = Query(default=1, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    customer = _get_customer(db, current_user)
    restaurant = _get_restaurant(db, restaurant_id)

    *_, km = _trip(restaurant, customer, delivery_pincode)

    return {
        "distance_km": km,
        "delivery_fee": float(food_delivery_fee(km)),
        "eta_minutes": predict_eta(km, items),
        "max_km": MAX_DELIVERY_KM,
        "deliverable": km <= MAX_DELIVERY_KM
    }


# Place Food Order
@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED
)
def place_food_order(
    data: FoodOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    customer = _get_customer(db, current_user)
    restaurant = _get_restaurant(db, data.restaurant_id)

    if not restaurant.is_open:
        raise HTTPException(
            status_code=400,
            detail="Restaurant is closed"
        )

    ids = [line.menu_item_id for line in data.items]

    menu = {
        m.id: m for m in db.query(MenuItem).filter(
            MenuItem.restaurant_id == restaurant.id,
            MenuItem.id.in_(ids)
        ).all()
    }

    items_total = Decimal("0.00")
    total_qty = 0
    order_items = []

    for line in data.items:

        item = menu.get(line.menu_item_id)

        if not item or not item.is_available:
            raise HTTPException(
                status_code=400,
                detail="An item in your cart is not available"
            )

        items_total += item.price * line.quantity
        total_qty += line.quantity

        order_items.append(
            OrderItem(
                item_name=item.name,
                price=item.price,
                quantity=line.quantity
            )
        )

    r_lat, r_lng, d_lat, d_lng, km = _trip(
        restaurant, customer, data.delivery_pincode
    )

    if km > MAX_DELIVERY_KM:
        raise HTTPException(
            status_code=400,
            detail=(
                f"This restaurant is {km:.1f} km away. "
                f"We deliver up to {MAX_DELIVERY_KM:.0f} km."
            )
        )

    new_order = Order(
        order_number=f"LS-{uuid4().hex[:10].upper()}",
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        pickup_address=f"{restaurant.name}, {restaurant.address}",
        pickup_pincode=restaurant.pincode,
        pickup_lat=r_lat,
        pickup_lng=r_lng,
        delivery_address=data.delivery_address,
        delivery_pincode=data.delivery_pincode,
        delivery_lat=d_lat,
        delivery_lng=d_lng,
        distance_km=Decimal(str(km)),
        eta_minutes=predict_eta(km, total_qty),
        package_description=f"Food from {restaurant.name}",
        delivery_charge=food_delivery_fee(km),
        items_total=items_total,
        items=order_items
    )

    db.add(new_order)
    db.flush()

    add_tracking(
        db, new_order, OrderStatus.pending,
        current_user.id, f"Order placed ({km:.1f} km trip)"
    )

    db.commit()
    db.refresh(new_order)

    notify_order(new_order, "order_new")

    return new_order