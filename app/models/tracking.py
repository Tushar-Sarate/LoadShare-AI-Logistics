from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.order import OrderStatus


class Tracking(Base):

    __tablename__ = "tracking"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer, ForeignKey("orders.id"), nullable=False, index=True
    )

    status = Column(Enum(OrderStatus), nullable=False)

    note = Column(String(255))

    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    order = relationship("Order")