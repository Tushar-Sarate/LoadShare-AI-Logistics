from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.order import PaymentStatus


class Payment(Base):

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer, ForeignKey("orders.id"), nullable=False, index=True
    )

    amount = Column(Numeric(10, 2), nullable=False)

    method = Column(String(30), nullable=False)   # UPI or COD

    reference = Column(String(50))                # UPI reference (UTR)

    status = Column(
        Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    order = relationship("Order")