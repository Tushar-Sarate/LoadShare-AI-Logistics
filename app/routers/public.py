from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order, OrderStatus
from app.models.restaurant import Restaurant
from app.schemas.restaurant_schema import RestaurantResponse
from app.services.rating_service import attach_ratings


router = APIRouter(
    prefix="/public",
    tags=["Public"]
)


# Restaurants for the public home page
@router.get("/restaurants", response_model=List[RestaurantResponse])
def public_restaurants(db: Session = Depends(get_db)):

    rows = db.query(Restaurant).order_by(Restaurant.name).all()

    return attach_ratings(db, rows)


# Numbers for the home page
@router.get("/stats")
def public_stats(db: Session = Depends(get_db)):

    return {
        "restaurants": db.query(Restaurant).count(),
        "cities": db.query(func.count(func.distinct(Restaurant.city))).scalar() or 0,
        "delivered_orders": db.query(Order).filter(
            Order.order_status == OrderStatus.delivered
        ).count(),
        "partners": db.query(DeliveryPartner).count(),
    }