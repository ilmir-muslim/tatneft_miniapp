from typing import Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app import file_storage
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
    if cheque_image:
        cheque_image_path = await file_storage.save_uploaded_file(cheque_image)

    db_order = models.Order(
        **order.model_dump(exclude={"cheque_image"}),
        user_id=user_id,
        status=models.OrderStatus.PENDING,
        cheque_image_path=cheque_image_path
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
    return db.query(models.Setting).first()


def update_settings(db: Session, settings: schemas.SettingsUpdate):
    db_settings = db.query(models.Setting).first()
    if db_settings:
        for key, value in settings.dict().items():
            setattr(db_settings, key, value)
        db.commit()
        db.refresh(db_settings)
    return db_settings
