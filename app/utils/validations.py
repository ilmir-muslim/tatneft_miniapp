from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import crud
from app.utils.price_parser import PriceParser  


price_parser = PriceParser()


def validate_azs_number(azs_number: int):
    """Проверяет, что номер АЗС находится в диапазоне 1-999"""
    if not (1 <= azs_number <= 999):
        raise HTTPException(
            status_code=422, detail="Номер АЗС должен быть в диапазоне от 1 до 999"
        )


