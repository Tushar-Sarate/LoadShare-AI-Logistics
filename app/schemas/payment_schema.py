from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from datetime import datetime
from typing import Literal, Optional

from app.models.order import PaymentStatus


# Create Payment
class PaymentCreate(BaseModel):

    order_id: int
    method: Literal["UPI", "COD"]
    reference: Optional[str] = Field(default=None, pattern=r"^\d{12}$")


# Payment Response
class PaymentResponse(BaseModel):

    id: int
    order_id: int
    amount: Decimal
    method: str
    reference: Optional[str] = None
    status: PaymentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)