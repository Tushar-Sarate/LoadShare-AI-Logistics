from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Review(Base):

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer, ForeignKey("orders.id"), nullable=False, unique=True
    )

    customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=False, index=True
    )

    restaurant_id = Column(
        Integer, ForeignKey("restaurants.id"), nullable=False, index=True
    )

    rating = Column(Integer, nullable=False)

    comment = Column(String(500))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )