from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Literal


# Create Complaint
class ComplaintCreate(BaseModel):

    order_id: Optional[int] = None
    subject: str = Field(min_length=5, max_length=150)
    description: str = Field(min_length=10)


# Update Complaint Status (admin)
class ComplaintStatusUpdate(BaseModel):

    status: Literal["Open", "In Progress", "Resolved"]


# Complaint Response
class ComplaintResponse(BaseModel):

    id: int
    customer_id: int
    order_id: Optional[int] = None
    subject: str
    description: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)