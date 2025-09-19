from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.utils.notifications import notify_new_order
from app.utils.validations import validate_azs_number, validate_column_number

from .dependencies import get_db
from . import crud, schemas
from .utils.price_parser import PriceParser

router = APIRouter()
price_parser = PriceParser()


@router.post("/orders/", response_model=schemas.Order)
async def create_order(
    user_id: int = Form(...),
    azs_number: int = Form(...),
    column_number: int = Form(...),
    fuel_type: str = Form(...),
    volume: float = Form(None),  
    amount: float = Form(None),  
    cheque_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # Проверяем что указан либо объем, либо сумма
    if volume is None and amount is None:
        raise HTTPException(
            status_code=422, detail="Необходимо указать объем или сумму"
        )

    # Валидация номера АЗС
    validate_azs_number(azs_number)

    # Валидация номера колонки для данной АЗС (использует кэш)
    validate_column_number(azs_number, column_number, db)

    order_data = schemas.OrderCreate(
        azs_number=azs_number,
        column_number=column_number,
        fuel_type=fuel_type,
        volume=volume,
        amount=amount,
    )

    order = await crud.create_order(
        db=db, order=order_data, user_id=user_id, cheque_image=cheque_image
    )

    # Отправляем уведомление о новом заказе
    await notify_new_order(
        {
            "id": order.id,
            "user_id": order.user_id,
            "azs_number": order.azs_number,
            "column_number": order.column_number,
            "fuel_type": order.fuel_type,
            "volume": order.volume,
            "amount": order.amount,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
        }
    )

    return order


@router.get("/orders/", response_model=List[schemas.Order])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = crud.get_orders(db, skip=skip, limit=limit)
    return orders


@router.get("/orders/{order_id}", response_model=schemas.Order)
def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order


@router.get("/settings/", response_model=schemas.Settings)
def get_settings(db: Session = Depends(get_db)):
    return crud.get_settings(db)


@router.get("/azs/{azs_number}", response_model=schemas.AzsResponse)
def get_azs_data(azs_number: int, db: Session = Depends(get_db)):
    validate_azs_number(azs_number)
    try:
        settings = crud.get_settings(db)
        # Передаем db как третий аргумент
        azs_data = price_parser.get_azs_data_with_discount(azs_number, settings, db)

        if "error" in azs_data:
            print(f"AZS {azs_number} error: {azs_data['error']}")
            raise HTTPException(status_code=404, detail=azs_data["error"])

        return azs_data
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
