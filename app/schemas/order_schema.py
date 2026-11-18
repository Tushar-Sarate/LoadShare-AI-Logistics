from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

from app.models.order import OrderStatus, PaymentStatus


# Create Order (parcel)
class OrderCreate(BaseModel):

    pickup_address: str = Field(min_length=5)
    pickup_pincode: str = Field(pattern=r"^\d{6}$")
    delivery_address: str = Field(min_length=5)
    delivery_pincode: str = Field(pattern=r"^\d{6}$")
    package_description: Optional[str] = None
    weight_kg: Decimal = Field(gt=0, le=50)


# Update Order Status
class OrderStatusUpdate(BaseModel):

    order_status: OrderStatus


# Food items inside an order
class OrderItemResponse(BaseModel):

    item_name: str
    price: Decimal
    quantity: int

    model_config = ConfigDict(from_attributes=True)


# Order Response
class OrderResponse(BaseModel):

    id: int
    order_number: str

    customer_id: int
    delivery_partner_id: Optional[int] = None

    restaurant_id: Optional[int] = None
    restaurant_name: Optional[str] = None

    pickup_address: str
    pickup_pincode: str
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None

    delivery_address: str
    delivery_pincode: str
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None

    package_description: Optional[str] = None
    weight_kg: Optional[Decimal] = None

    distance_km: Optional[Decimal] = None
    eta_minutes: Optional[int] = None

    delivery_charge: Decimal
    items_total: Decimal = Decimal("0.00")
    items: List[OrderItemResponse] = []

    payment_status: PaymentStatus
    payment_method: Optional[str] = None
    order_status: OrderStatus

    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)