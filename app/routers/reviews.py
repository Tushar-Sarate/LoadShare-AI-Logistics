from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.review import Review
from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)


class ReviewCreate(BaseModel):

    order_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=500)


class ReviewResponse(BaseModel):

    id: int
    order_id: int
    restaurant_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def _customer(db: Session, user: User) -> Customer:

    if user.role != "customer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can write reviews"
        )

    customer = db.query(Customer).filter(
        Customer.user_id == user.id
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile not found")

    return customer


# Rate a delivered order
@router.post(
    "/",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED
)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    customer = _customer(db, current_user)

    order = db.query(Order).filter(
        Order.id == data.order_id,
        Order.customer_id == customer.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.restaurant_id is None:
        raise HTTPException(
            status_code=400,
            detail="Only restaurant orders can be rated"
        )

    if order.order_status != OrderStatus.delivered:
        raise HTTPException(
            status_code=400,
            detail="You can rate an order after it is delivered"
        )

    if db.query(Review).filter(Review.order_id == order.id).first():
        raise HTTPException(
            status_code=400,
            detail="You already reviewed this order"
        )

    review = Review(
        order_id=order.id,
        customer_id=customer.id,
        restaurant_id=order.restaurant_id,
        rating=data.rating,
        comment=(data.comment or None)
    )

    db.add(review)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="You already reviewed this order"
        )

    db.refresh(review)

    return review


# Which of my orders did I already rate
@router.get("/mine")
def my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    customer = _customer(db, current_user)

    rows = db.query(Review).filter(
        Review.customer_id == customer.id
    ).all()

    return [{"order_id": r.order_id, "rating": r.rating} for r in rows]


# Latest reviews of a restaurant
@router.get("/restaurant/{restaurant_id}")
def restaurant_reviews(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    rows = (
        db.query(Review, User.full_name)
        .join(Customer, Customer.id == Review.customer_id)
        .join(User, User.id == Customer.user_id)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "rating": r.rating,
            "comment": r.comment,
            "customer": (name.split()[0] if name else "Customer"),
            "created_at": r.created_at,
        }
        for r, name in rows
    ]