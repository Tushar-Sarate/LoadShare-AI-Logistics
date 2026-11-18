import enum
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    Numeric, DateTime, Text, Enum, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class OrderStatus(str, enum.Enum):
    pending = "Pending"
    assigned = "Assigned"
    picked_up = "Picked Up"
    in_transit = "In Transit"
    delivered = "Delivered"
    cancelled = "Cancelled"


class PaymentStatus(str, enum.Enum):
    pending = "Pending"
    paid = "Paid"
    failed = "Failed"
    refunded = "Refunded"


class Order(Base):

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    order_number = Column(
        String(50), unique=True, nullable=False, index=True
    )

    customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=False, index=True
    )

    delivery_partner_id = Column(
        Integer,
        ForeignKey("delivery_partners.id"),
        nullable=True,
        index=True
    )

    restaurant_id = Column(
        Integer, ForeignKey("restaurants.id"), nullable=True
    )

    pickup_address = Column(Text, nullable=False)

    pickup_pincode = Column(String(10), nullable=False)

    pickup_lat = Column(Float)

    pickup_lng = Column(Float)

    delivery_address = Column(Text, nullable=False)

    delivery_pincode = Column(String(10), nullable=False)

    delivery_lat = Column(Float)

    delivery_lng = Column(Float)

    # trip distance and predicted delivery time
    distance_km = Column(Numeric(6, 2))

    eta_minutes = Column(Integer)

    package_description = Column(String(255))

    weight_kg = Column(Numeric(6, 2))

    # delivery fee
    delivery_charge = Column(Numeric(10, 2), nullable=False)

    # total price of the food items
    items_total = Column(
        Numeric(10, 2), default=0, nullable=False, server_default="0"
    )

    payment_status = Column(
        Enum(PaymentStatus),
        default=PaymentStatus.pending,
        nullable=False
    )

    # UPI or COD (set when the customer chooses)
    payment_method = Column(String(10))

    order_status = Column(
        Enum(OrderStatus),
        default=OrderStatus.pending,
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    customer = relationship("Customer")

    delivery_partner = relationship("DeliveryPartner")

    restaurant = relationship("Restaurant", lazy="selectin")

    items = relationship("OrderItem", lazy="selectin")

    @property
    def restaurant_name(self):
        return self.restaurant.name if self.restaurant else None