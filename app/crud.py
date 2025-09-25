from sqlalchemy.orm import Session

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
