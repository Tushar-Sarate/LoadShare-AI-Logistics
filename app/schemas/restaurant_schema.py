from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import List, Optional


# Create Restaurant (admin)
class RestaurantCreate(BaseModel):

    name: str = Field(min_length=2, max_length=100)
    cuisine: str = Field(min_length=2, max_length=100)
    emoji: str = Field(default="🍽️", max_length=8)
    image_url: Optional[str] = Field(default=None, max_length=500, pattern=r"^https?://")
    address: str = Field(min_length=5, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    pincode: str = Field(pattern=r"^\d{6}$")


class RestaurantResponse(BaseModel):

    id: int
    name: str
    cuisine: Optional[str] = None
    emoji: Optional[str] = None
    image_url: Optional[str] = None
    address: str
    city: Optional[str] = None
    pincode: str
    is_open: bool
    rating: Optional[float] = None
    rating_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# Create Menu Item (admin)
class MenuItemCreate(BaseModel):

    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    price: Decimal = Field(gt=0, le=5000)
    is_veg: bool = True


class MenuItemResponse(BaseModel):

    id: int
    restaurant_id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    is_veg: bool
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


# Food Order
class FoodOrderLine(BaseModel):

    menu_item_id: int
    quantity: int = Field(ge=1, le=20)


class FoodOrderCreate(BaseModel):

    restaurant_id: int
    items: List[FoodOrderLine] = Field(min_length=1, max_length=30)
    delivery_address: str = Field(min_length=5)
    delivery_pincode: str = Field(pattern=r"^\d{6}$")