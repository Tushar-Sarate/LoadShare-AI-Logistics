from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.restaurant import Restaurant, MenuItem

from app.schemas.restaurant_schema import (
    RestaurantCreate,
    RestaurantResponse,
    MenuItemCreate,
    MenuItemResponse
)

from app.services.rating_service import attach_ratings

from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/restaurants",
    tags=["Restaurants"]
)


# List Restaurants (with average rating)
@router.get(
    "/",
    response_model=List[RestaurantResponse]
)
def list_restaurants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    rows = db.query(Restaurant).order_by(Restaurant.name).all()

    return attach_ratings(db, rows)


# Get Menu of a Restaurant
@router.get(
    "/{restaurant_id}/menu",
    response_model=List[MenuItemResponse]
)
def get_menu(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    return db.query(MenuItem).filter(
        MenuItem.restaurant_id == restaurant_id
    ).order_by(MenuItem.id).all()


# Add Restaurant (admin only)
@router.post(
    "/",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED
)
def create_restaurant(
    data: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can add restaurants"
        )

    restaurant = Restaurant(
        name=data.name,
        cuisine=data.cuisine,
        emoji=data.emoji,
        image_url=data.image_url or None,
        address=data.address,
        city=data.city,
        pincode=data.pincode
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


# Add Menu Item (admin only)
@router.post(
    "/{restaurant_id}/menu",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED
)
def add_menu_item(
    restaurant_id: int,
    data: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can add menu items"
        )

    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    item = MenuItem(
        restaurant_id=restaurant_id,
        name=data.name,
        description=data.description,
        price=data.price,
        is_veg=data.is_veg
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item