from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Complaint(Base):

    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=False, index=True
    )

    order_id = Column(
        Integer, ForeignKey("orders.id"), nullable=True
    )

    subject = Column(String(150), nullable=False)

    description = Column(Text, nullable=False)

    status = Column(String(30), default="Open", nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    customer = relationship("Customer")

    order = relationship("Order")