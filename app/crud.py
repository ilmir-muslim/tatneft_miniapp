import os
from typing import Optional
from fastapi import UploadFile
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.utils import file_storage
from . import models, schemas


def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Order).offset(skip).limit(limit).all()


async def create_order(
    db: Session,
    order: schemas.OrderCreate,
    user_id: int,
    cheque_image: Optional[UploadFile] = None,
):
    cheque_image_path = None
    cheque_image_url = None

    if cheque_image:
        try:
            # Сохраняем файл и получаем путь
            cheque_image_path = await file_storage.save_uploaded_file(cheque_image)
            cheque_image_url = f"/uploads/{os.path.basename(cheque_image_path)}"
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Ошибка при сохранении файла: {str(e)}"
            )

    # Создаем объект заказа
    db_order = models.Order(
        user_id=user_id,
        azs_number=order.azs_number,
        column_number=order.column_number,
        fuel_type=order.fuel_type,
        volume=order.volume,
        amount=order.amount,
        status=models.OrderStatus.PENDING,
        cheque_image_path=cheque_image_path,
        cheque_image_url=cheque_image_url,
    )

    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def update_order_status(
    db: Session, order_id: int, status: str, rejection_reason: str = None
):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if db_order:
        db_order.status = status
        if rejection_reason:
            db_order.rejection_reason = rejection_reason
        db.commit()
        db.refresh(db_order)
    return db_order


def get_settings(db: Session):
    settings = db.query(models.Setting).first()
    if not settings:
        # Создаем настройки по умолчанию
        settings = models.Setting(
            discount_type="percent",
            discount_value=0,
            payment_instructions="Оплатите заказ по реквизитам...",
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(db: Session, settings: schemas.SettingsUpdate):
    db_settings = db.query(models.Setting).first()
    if db_settings:
        for key, value in settings.model_dump().items():
            setattr(db_settings, key, value)
    else:
        # Создаем новые настройки если их нет
        db_settings = models.Setting(**settings.model_dump())
        db.add(db_settings)

    db.commit()
    db.refresh(db_settings)
    return db_settings
