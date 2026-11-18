from sqlalchemy import Column, Integer, String, ForeignKey, Numeric

from app.database import Base


class OrderItem(Base):

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer, ForeignKey("orders.id"), nullable=False, index=True
    )

    item_name = Column(String(100), nullable=False)

    price = Column(Numeric(8, 2), nullable=False)

    quantity = Column(Integer, nullable=False)