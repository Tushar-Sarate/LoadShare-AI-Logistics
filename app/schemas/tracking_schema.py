from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

from app.models.order import OrderStatus


# Tracking Response
class TrackingResponse(BaseModel):

    id: int
    order_id: int
    status: OrderStatus
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)