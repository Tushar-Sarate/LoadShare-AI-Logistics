from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User

from app.schemas.user_schema import UserResponse

from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/users",
    tags=["User Management"]
)


# List All Users (admin only)
@router.get(
    "/",
    response_model=List[UserResponse]
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can view users"
        )

    return db.query(User).order_by(User.id).all()


# Activate / Deactivate User (admin only)
@router.patch(
    "/{user_id}/active",
    response_model=UserResponse
)
def set_user_active(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can change user status"
        )

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account"
        )

    user.is_active = is_active

    db.commit()

    db.refresh(user)

    return user