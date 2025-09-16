from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class OrderStatus(str, Enum):
    PENDING = "ожидание"
    ACCEPTED = "принято"
    REJECTED = "отказано"


class OrderBase(BaseModel):
    azs_number: int
    column_number: int
    fuel_type: str
    volume: float
    amount: float


class OrderCreate(OrderBase):
    cheque_image: Optional[bytes] = None


class Order(OrderBase):
    id: int
    user_id: int
    status: OrderStatus
    created_at: datetime
    cheque_image_url: Optional[str] = None
    cheque_image_path: Optional[str] = None
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True


class SettingsBase(BaseModel):
    discount_type: str
    discount_value: float
    payment_instructions: str


class SettingsUpdate(SettingsBase):
    pass


class Settings(SettingsBase):
    id: int

    class Config:
        from_attributes = True


class FuelSchema(BaseModel):
    fuel_type_id: int
    name: str
    price: float
    discount_price: Optional[float] = None
    currency_code: str
    updated: Optional[float] = None
    color: Optional[str] = None
    filter_group: Optional[str] = None


class AzsResponse(BaseModel):
    azs_number: int
    address: str
    region: Optional[str] = None
    fuel: list[FuelSchema]
    actualization_date: Optional[float] = None
