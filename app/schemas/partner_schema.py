from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional

PHONE_PATTERN = r"^[6-9]\d{9}$"
PINCODE_PATTERN = r"^\d{6}$"


def _clean_vehicle_number(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return value.replace(" ", "").replace("-", "").upper()


class PartnerCreate(BaseModel):

    phone: str = Field(pattern=PHONE_PATTERN)
    vehicle_type: str = Field(min_length=2, max_length=50)
    vehicle_number: str = Field(min_length=5, max_length=20)
    city: str = Field(min_length=2, max_length=100)
    pincode: str = Field(pattern=PINCODE_PATTERN)

    @field_validator("vehicle_number")
    @classmethod
    def clean_vehicle_number(cls, v):
        return _clean_vehicle_number(v)


class PartnerUpdate(BaseModel):

    phone: Optional[str] = Field(default=None, pattern=PHONE_PATTERN)
    vehicle_type: Optional[str] = Field(default=None, min_length=2, max_length=50)
    vehicle_number: Optional[str] = Field(default=None, min_length=5, max_length=20)
    city: Optional[str] = Field(default=None, min_length=2, max_length=100)
    pincode: Optional[str] = Field(default=None, pattern=PINCODE_PATTERN)

    @field_validator("vehicle_number")
    @classmethod
    def clean_vehicle_number(cls, v):
        return _clean_vehicle_number(v)


class PartnerResponse(BaseModel):

    id: int
    user_id: int
    phone: str
    vehicle_type: str
    vehicle_number: str
    city: Optional[str] = None
    pincode: Optional[str] = None
    is_available: bool

    model_config = ConfigDict(from_attributes=True)