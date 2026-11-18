
from pydantic import BaseModel, Field
from typing import Optional


class CustomerCreate(BaseModel):

    phone: str = Field(min_length=10, max_length=15)
    address: str = Field(min_length=5, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    pincode: str = Field(min_length=6, max_length=10)


class CustomerUpdate(BaseModel):

    phone: Optional[str] = Field(default=None, min_length=10, max_length=15)
    address: Optional[str] = Field(default=None, min_length=5, max_length=255)
    city: Optional[str] = Field(default=None, min_length=2, max_length=100)
    pincode: Optional[str] = Field(default=None, min_length=6, max_length=10)


class CustomerResponse(BaseModel):

    id: int
    user_id: int
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    pincode: Optional[str]

    model_config = {"from_attributes": True}
