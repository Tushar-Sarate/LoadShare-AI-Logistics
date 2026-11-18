from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship

from app.database import Base
from app.services.geo_service import register_geo


class DeliveryPartner(Base):

    __tablename__ = "delivery_partners"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    phone = Column(String(15), unique=True, nullable=False)

    vehicle_type = Column(String(50))

    vehicle_number = Column(String(20), unique=True, nullable=False)

    city = Column(String(100))

    pincode = Column(String(10))

    latitude = Column(Float)

    longitude = Column(Float)

    is_available = Column(Boolean, default=True, nullable=False)

    user = relationship("User")


# Latitude and longitude are filled automatically from city and pincode
register_geo(DeliveryPartner)