
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.delivery_partner import DeliveryPartner

from app.schemas.partner_schema import (
    PartnerCreate,
    PartnerUpdate,
    PartnerResponse
)

from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/partners",
    tags=["Delivery Partner Management"]
)


# Create Delivery Partner Profile
@router.post(
    "/profile",
    response_model=PartnerResponse,
    status_code=status.HTTP_201_CREATED
)
def create_partner_profile(
    data: PartnerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "delivery_partner":
        raise HTTPException(
            status_code=403,
            detail="Only delivery partners can create this profile"
        )

    existing_profile = db.query(DeliveryPartner).filter(
        DeliveryPartner.user_id == current_user.id
    ).first()

    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Delivery partner profile already exists"
        )

    existing_phone = db.query(DeliveryPartner).filter(
        DeliveryPartner.phone == data.phone
    ).first()

    if existing_phone:
        raise HTTPException(
            status_code=400,
            detail="Phone number already registered"
        )

    existing_vehicle = db.query(DeliveryPartner).filter(
        DeliveryPartner.vehicle_number == data.vehicle_number
    ).first()

    if existing_vehicle:
        raise HTTPException(
            status_code=400,
            detail="Vehicle number already registered"
        )

    # Create Delivery Partner
    new_partner = DeliveryPartner(
        user_id=current_user.id,
        phone=data.phone,
        vehicle_type=data.vehicle_type,
        vehicle_number=data.vehicle_number,
        city=data.city,
        pincode=data.pincode
    )

    db.add(new_partner)
    db.commit()
    db.refresh(new_partner)

    return new_partner


# Get Delivery Partner Profile
@router.get(
    "/profile",
    response_model=PartnerResponse
)
def get_partner_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "delivery_partner":
        raise HTTPException(
            status_code=403,
            detail="Only delivery partners can access this profile"
        )

    partner = db.query(DeliveryPartner).filter(
        DeliveryPartner.user_id == current_user.id
    ).first()

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Delivery partner profile not found"
        )

    return partner


# Update Delivery Partner Profile
@router.patch(
    "/profile",
    response_model=PartnerResponse
)
def update_partner_profile(
    data: PartnerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "delivery_partner":
        raise HTTPException(
            status_code=403,
            detail="Only delivery partners can update this profile"
        )

    partner = db.query(DeliveryPartner).filter(
        DeliveryPartner.user_id == current_user.id
    ).first()

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Delivery partner profile not found"
        )

    update_data = data.model_dump(exclude_unset=True)

    # Check duplicate phone
    if "phone" in update_data:
        existing_phone = db.query(DeliveryPartner).filter(
            DeliveryPartner.phone == update_data["phone"],
            DeliveryPartner.id != partner.id
        ).first()

        if existing_phone:
            raise HTTPException(
                status_code=400,
                detail="Phone number already registered"
            )

    # Check duplicate vehicle number
    if "vehicle_number" in update_data:
        existing_vehicle = db.query(DeliveryPartner).filter(
            DeliveryPartner.vehicle_number == update_data["vehicle_number"],
            DeliveryPartner.id != partner.id
        ).first()

        if existing_vehicle:
            raise HTTPException(
                status_code=400,
                detail="Vehicle number already registered"
            )

    # Update profile fields
    for key, value in update_data.items():
        setattr(partner, key, value)

    db.commit()
    db.refresh(partner)

    return partner
