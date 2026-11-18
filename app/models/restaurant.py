from sqlalchemy import Column, Integer, String, Boolean, Numeric, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.services.geo_service import register_geo


class Restaurant(Base):

    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    cuisine = Column(String(100))

    emoji = Column(String(8), default="🍽️")

    image_url = Column(String(500))

    address = Column(String(255), nullable=False)

    city = Column(String(100))

    pincode = Column(String(10), nullable=False, index=True)

    latitude = Column(Float)

    longitude = Column(Float)

    is_open = Column(Boolean, default=True, nullable=False)


class MenuItem(Base):

    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)

    restaurant_id = Column(
        Integer, ForeignKey("restaurants.id"), nullable=False, index=True
    )

    name = Column(String(100), nullable=False)

    description = Column(String(255))

    price = Column(Numeric(8, 2), nullable=False)

    is_veg = Column(Boolean, default=True, nullable=False)

    is_available = Column(Boolean, default=True, nullable=False)

    restaurant = relationship("Restaurant")


# Latitude and longitude are filled automatically from city and pincode
register_geo(Restaurant)