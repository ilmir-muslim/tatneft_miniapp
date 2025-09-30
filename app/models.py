from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Text, Enum, JSON
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from .database import Base


class OrderStatus(PyEnum):
    PENDING = "ожидание"
    ACCEPTED = "принято"
    REJECTED = "отказано"


class PaymentStatus(PyEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    azs_number = Column(Integer)
    column_number = Column(Integer)
    fuel_type = Column(String(50))
    fuel_price = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    rejection_reason = Column(Text)
    payment_id = Column(String(255))  # ID платежа в системе банка
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_data = Column(JSON)  # Дополнительные данные платежа


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    discount_type = Column(Enum("percent", "fixed"))
    discount_value = Column(Float)
    payment_instructions = Column(Text)
    alfa_login = Column(String(100))  # Логин API Альфа-Банка
    alfa_password = Column(String(100))  # Пароль API Альфа-Банка
    alfa_token = Column(String(500))  # Токен API Альфа-Банка
    alfa_token_expires = Column(DateTime)  # Время истечения токена

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(500), unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_activity = Column(DateTime, server_default=func.now())
