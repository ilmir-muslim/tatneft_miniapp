from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum, JSON
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from .database import Base


class OrderStatus(PyEnum):
    PENDING = "ожидание"
    ACCEPTED = "принято"
    REJECTED = "отказано"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    azs_number = Column(Integer)
    column_number = Column(Integer)
    fuel_type = Column(String(50))
    volume = Column(Float)
    amount = Column(Float)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    rejection_reason = Column(Text)
    cheque_image_url = Column(String(255))
    cheque_image_path = Column(String(255))


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    discount_type = Column(Enum("percent", "fixed"))
    discount_value = Column(Float)
    payment_instructions = Column(Text)


class PriceCache(Base):
    __tablename__ = "price_cache"

    id = Column(Integer, primary_key=True)
    azs_number = Column(Integer, unique=True)
    prices_data = Column(JSON)  # Хранение цен в формате JSON
    updated_at = Column(DateTime, default=func.now())
