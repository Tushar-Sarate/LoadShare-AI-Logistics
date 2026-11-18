
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.customer import Customer

from app.schemas.customer_schema import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse
)

from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/customers",
    tags=["Customer Management"]
)


# Create Customer Profile
@router.post(
    "/profile",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED
)
def create_customer_profile(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "customer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can create customer profiles"
        )

    existing_profile = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Customer profile already exists"
        )

    existing_phone = db.query(Customer).filter(
        Customer.phone == data.phone
    ).first()

    if existing_phone:
        raise HTTPException(
            status_code=400,
            detail="Phone number already registered"
        )

    new_customer = Customer(
        user_id=current_user.id,
        phone=data.phone,
        address=data.address,
        city=data.city,
        pincode=data.pincode
    )

    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    return new_customer


# Get Customer Profile
@router.get(
    "/profile",
    response_model=CustomerResponse
)
def get_customer_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    return customer


# Update Customer Profile
@router.patch(
    "/profile",
    response_model=CustomerResponse
)
def update_customer_profile(
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    update_data = data.model_dump(exclude_unset=True)

    if "phone" in update_data:
        existing_phone = db.query(Customer).filter(
            Customer.phone == update_data["phone"],
            Customer.id != customer.id
        ).first()

        if existing_phone:
            raise HTTPException(
                status_code=400,
                detail="Phone number already registered"
            )

    for key, value in update_data.items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)

    return customer
