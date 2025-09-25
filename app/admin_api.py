from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .dependencies import get_db
from . import crud, schemas
from .admin_auth import get_current_admin, create_access_token

router = APIRouter()


@router.post("/login")
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != "admin" or form_data.password != "admin123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/orders/", response_model=List[schemas.Order])
def get_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    return crud.get_orders(db, skip=skip, limit=limit)


@router.get("/orders/{order_id}", response_model=schemas.Order)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    db_order = crud.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order


@router.patch("/orders/{order_id}")
def update_order_status(
    order_id: int,
    status_update: dict,  # Принимаем JSON как словарь
    rejection_reason: str = None,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    # Извлекаем статус из JSON
    status_value = status_update.get("status")
    if not status_value:
        raise HTTPException(status_code=422, detail="Status is required")

    return crud.update_order_status(db, order_id, status_value, rejection_reason)


@router.get("/settings/", response_model=schemas.Settings)
def get_settings(
    db: Session = Depends(get_db), admin: str = Depends(get_current_admin)
):
    return crud.get_settings(db)


# В app/admin_api.py - при изменении настроек скидок
@router.put("/settings/", response_model=schemas.Settings)
def update_settings(
    settings: schemas.SettingsUpdate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    updated_settings = crud.update_settings(db, settings)

    # Очищаем кэш всех АЗС при изменении скидок
    try:
        from app.utils.price_parser import price_parser

        price_parser.clear_all_cache()
        print("Кэш всех АЗС очищен из-за изменения настроек скидок")
    except Exception as e:
        print(f"Ошибка при очистке кэша настроек: {e}")

    return updated_settings
