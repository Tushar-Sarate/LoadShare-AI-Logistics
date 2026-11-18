from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.customer import Customer
from app.models.order import Order
from app.models.complaint import Complaint

from app.schemas.complaint_schema import (
    ComplaintCreate,
    ComplaintStatusUpdate,
    ComplaintResponse
)

from app.services.realtime import publish
from app.services.email_service import send_email
from app.services.support_agent import process_complaint

from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"]
)


# Create Complaint
@router.post(
    "/",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED
)
def create_complaint(
    data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "customer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can create complaints"
        )

    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    order = None

    if data.order_id is not None:

        order = db.query(Order).filter(
            Order.id == data.order_id,
            Order.customer_id == customer.id
        ).first()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

    new_complaint = Complaint(
        customer_id=customer.id,
        order_id=data.order_id,
        subject=data.subject,
        description=data.description
    )

    db.add(new_complaint)

    db.commit()

    db.refresh(new_complaint)

    publish(set(), {"admin"}, {"type": "complaint_new"})

    # AI support agent replies by email
    try:
        reply, _ = process_complaint(db, new_complaint, current_user, order)
        send_email(
            current_user.email,
            f"Complaint #{new_complaint.id}: {new_complaint.subject}",
            reply
        )
        db.refresh(new_complaint)
    except Exception as e:
        print(f"[support] complaint auto-reply failed: {e}")

    return new_complaint


# List Complaints
@router.get(
    "/",
    response_model=List[ComplaintResponse]
)
def list_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    query = db.query(Complaint)

    if current_user.role == "customer":

        customer = db.query(Customer).filter(
            Customer.user_id == current_user.id
        ).first()

        if not customer:
            return []

        query = query.filter(
            Complaint.customer_id == customer.id
        )

    elif current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not allowed to view complaints"
        )

    return query.order_by(Complaint.created_at.desc()).all()


# Update Complaint Status (admin only)
@router.patch(
    "/{complaint_id}/status",
    response_model=ComplaintResponse
)
def update_complaint_status(
    complaint_id: int,
    data: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can update complaint status"
        )

    complaint = db.query(Complaint).filter(
        Complaint.id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    complaint.status = data.status

    db.commit()

    db.refresh(complaint)

    # Tell the customer by email
    try:
        owner = complaint.customer.user
        send_email(
            owner.email,
            f"Complaint #{complaint.id} is now: {complaint.status}",
            f"Hi {owner.full_name},\n\nYour complaint \"{complaint.subject}\" "
            f"is now marked as {complaint.status}.\n\nLoadShare Support"
        )
    except Exception as e:
        print(f"[support] status email skipped: {e}")

    return complaint