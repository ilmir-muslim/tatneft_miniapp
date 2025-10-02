from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union


class OrderStatus(str, Enum):
    PENDING = "ожидание"
    ACCEPTED = "принято"
    REJECTED = "отказано"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class OrderBase(BaseModel):
    azs_number: int
    column_number: int
    fuel_type: str
    fuel_price: float
    volume: Optional[float] = None
    amount: Optional[float] = None
    user_id: int

    class Config:
        json_encoders = {OrderStatus: lambda v: v.value}


class OrderCreate(OrderBase):
    status: OrderStatus = OrderStatus.PENDING
    azs_id: Optional[int] = None


class Order(OrderBase):
    id: int
    status: OrderStatus
    created_at: datetime
    rejection_reason: Optional[str] = None
    cheque_image_url: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            OrderStatus: lambda v: v.value,
            datetime: lambda v: v.isoformat(),
        }

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Преобразуем enum в строку
        if "status" in data and isinstance(data["status"], OrderStatus):
            data["status"] = data["status"].value
        # Преобразуем datetime в строку
        if "created_at" in data and isinstance(data["created_at"], datetime):
            data["created_at"] = data["created_at"].isoformat()
        return data


class SettingsBase(BaseModel):
    discount_type: str = Field(..., pattern="^(percent|fixed)$")
    discount_value: float = Field(..., ge=0)
    payment_instructions: str
    alfa_login: Optional[str] = None
    alfa_password: Optional[str] = None
    use_payment_emulator: bool = Field(default=True)


class SettingsUpdate(SettingsBase):
    pass


class Settings(SettingsBase):
    id: int
    alfa_token: Optional[str] = None
    alfa_token_expires: Optional[datetime] = None

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


class AzsBaseResponse(BaseModel):
    id: Optional[int] = None  # Добавляем поле ID
    azs_number: int
    address: str
    region: Optional[str] = None
    fuel: list[FuelSchema]
    actualization_date: Optional[float] = None


class AzsWithCoords(AzsBaseResponse):
    lat: Optional[float] = None
    lon: Optional[float] = None
    distance: Optional[float] = None


class PaymentRequest(BaseModel):
    return_url: str


class PaymentResponse(BaseModel):
    payment_url: str
    payment_id: str
    order_id: int


class AzsSelectionResponse(BaseModel):
    need_selection: bool
    azs_list: Optional[List] = None
    azs_number: Optional[int] = None


# Добавить после существующих схем


class UserBase(BaseModel):
    username: str
    phone: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    login: str  # username, phone или email
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class SessionBase(BaseModel):
    token: str
    expires_at: datetime


class SessionCreate(SessionBase):
    user_id: int


class Session(SessionBase):
    id: int
    created_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True


AzsResponse = Union[AzsSelectionResponse, AzsBaseResponse]
