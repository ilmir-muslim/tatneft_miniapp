from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.utils.auth import (
    ACCESS_TOKEN_EXPIRE_DAYS,
    generate_session_token,
    get_password_hash,
    verify_password,
)

from . import models, schemas


def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_orders(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Order)
        .order_by(models.Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


async def create_order(db: Session, order: schemas.OrderCreate):
    """Создание заказа с данными из JSON"""
    db_order = models.Order(
        user_id=order.user_id,
        azs_number=order.azs_number,
        column_number=order.column_number,
        fuel_type=order.fuel_type,
        fuel_price=order.fuel_price,
        volume=order.volume,
        amount=order.amount,
        status=models.OrderStatus.PENDING,
    )
    # Если есть azs_id, сохраняем его
    if hasattr(order, "azs_id") and order.azs_id:
        db_order.azs_id = order.azs_id

    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def update_order_status(
    db: Session, order_id: int, status: str, rejection_reason: str = None
):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if db_order:
        # Преобразуем строку в Enum
        if status == "принято":
            db_order.status = models.OrderStatus.ACCEPTED
        elif status == "отказано":
            db_order.status = models.OrderStatus.REJECTED
        elif status == "ожидание":
            db_order.status = models.OrderStatus.PENDING
        else:
            # Если статус не распознан, оставляем текущий
            pass

        if rejection_reason:
            db_order.rejection_reason = rejection_reason
        db.commit()
        db.refresh(db_order)
    return db_order


def update_order_payment_status(
    db: Session,
    order_id: int,
    payment_status: str,
    payment_id: str = None,
    payment_data: dict = None,
):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if db_order:
        # Преобразуем строку в Enum для payment_status
        if payment_status == "succeeded":
            db_order.payment_status = models.PaymentStatus.SUCCEEDED
        elif payment_status == "failed":
            db_order.payment_status = models.PaymentStatus.FAILED
        elif payment_status == "pending":
            db_order.payment_status = models.PaymentStatus.PENDING
        elif payment_status == "canceled":
            db_order.payment_status = models.PaymentStatus.CANCELED
        elif payment_status == "refunded":
            db_order.payment_status = models.PaymentStatus.REFUNDED

        if payment_id:
            db_order.payment_id = payment_id
        if payment_data:
            db_order.payment_data = payment_data
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
        for key, value in settings.model_dump(exclude_unset=True).items():
            setattr(db_settings, key, value)
    else:
        db_settings = models.Setting(**settings.model_dump())
        db.add(db_settings)

    db.commit()
    db.refresh(db_settings)
    return db_settings


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_phone(db: Session, phone: str):
    return db.query(models.User).filter(models.User.phone == phone).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_login(db: Session, login: str):
    return (
        db.query(models.User)
        .filter(
            or_(
                models.User.username == login,
                models.User.phone == login,
                models.User.email == login,
            )
        )
        .first()
    )


def create_user(db: Session, user: schemas.UserCreate):
    # Проверяем уникальность username, phone, email
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    if user.phone and get_user_by_phone(db, user.phone):
        raise HTTPException(status_code=400, detail="Phone already registered")

    if user.email and get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        phone=user.phone,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, login: str, password: str):
    user = get_user_by_login(db, login)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_user_session(db: Session, user_id: int):
    token = generate_session_token()
    expires_at = datetime.now() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    # Удаляем старые сессии пользователя
    db.query(models.UserSession).filter(models.UserSession.user_id == user_id).delete()

    db_session = models.UserSession(user_id=user_id, token=token, expires_at=expires_at)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_user_session(db: Session, token: str):
    session = (
        db.query(models.UserSession)
        .filter(
            models.UserSession.token == token,
            models.UserSession.expires_at > datetime.now(),
        )
        .first()
    )

    if session:
        # Обновляем время последней активности
        session.last_activity = datetime.now()
        db.commit()
        db.refresh(session)

    return session


def delete_user_session(db: Session, token: str):
    session = (
        db.query(models.UserSession).filter(models.UserSession.token == token).first()
    )

    if session:
        db.delete(session)
        db.commit()
        return True
    return False


def get_current_user(db: Session, token: str):
    session = get_user_session(db, token)
    if not session:
        return None

    return db.query(models.User).filter(models.User.id == session.user_id).first()
