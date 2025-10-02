from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from math import radians, sin, cos, sqrt, atan2

from app.utils.notifications import notify_new_order
from app.utils.validations import validate_azs_number
from app.utils.alfa_payment import AlfaPayment
from app.utils.auth import create_access_token, verify_password
from .utils.alfa_payment_emulator import alfa_emulator

from .dependencies import get_db
from . import crud, schemas
from .utils.price_parser import PriceParser

router = APIRouter()
price_parser = PriceParser()
alfa_payment = AlfaPayment()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/orders/", response_model=schemas.Order)
async def create_order(
    order_data: schemas.OrderCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Создание заказа через JSON"""
    current_user = crud.get_current_user(db, token)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    order_dict = order_data.model_dump()
    if "status" in order_dict and isinstance(order_dict["status"], schemas.OrderStatus):
        order_dict["status"] = order_dict["status"].value

    order_dict["user_id"] = current_user.id
    print(f"Received order data from user {current_user.id}: {order_dict}")

    try:
        # Проверка объема и суммы
        if order_data.volume is None and order_data.amount is None:
            raise HTTPException(
                status_code=422, detail="Необходимо указать объем или сумму"
            )
        if order_data.volume is not None and order_data.amount is not None:
            raise HTTPException(
                status_code=422,
                detail="Укажите только объем ИЛИ сумму, не оба параметра",
            )

        # Валидация номера АЗС
        validate_azs_number(order_data.azs_number)

        # Создаем заказ
        order = await crud.create_order(db=db, order=schemas.OrderCreate(**order_dict))

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
                "status": order.status.value,
                "created_at": order.created_at.isoformat(),
            }
        )

        print(f"Order created successfully: ID={order.id}")
        try:
            # Очищаем кэш для конкретной АЗС
            azs_id = getattr(order_data, "azs_id", None)
            price_parser.clear_azs_cache(order_data.azs_number, azs_id)
            print(
                f"Кэш очищен для АЗС {order_data.azs_number} (ID: {azs_id or 'не указан'})"
            )
        except Exception as e:
            print(f"Ошибка при очистке кэша: {e}")
        return order

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/orders/{order_id}/payment", response_model=schemas.PaymentResponse)
async def create_payment(
    order_id: int,
    payment_request: schemas.PaymentRequest,
    db: Session = Depends(get_db),
):
    """Создание платежа через JSON"""
    # Получаем заказ
    order = crud.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Создаем платеж в Альфа-Банке
    payment_data = await alfa_payment.create_payment(
        db, order, payment_request.return_url
    )

    if not payment_data or "formUrl" not in payment_data:
        raise HTTPException(status_code=500, detail="Failed to create payment")

    # Обновляем информацию о платеже в заказе
    crud.update_order_payment_status(
        db,
        order_id,
        payment_status="pending",
        payment_id=payment_data.get("orderId"),
        payment_data=payment_data,
    )

    return {
        "payment_url": payment_data["formUrl"],
        "payment_id": payment_data["orderId"],
        "order_id": order_id,
    }


@router.post("/webhook/alfa")
async def alfa_webhook(data: dict, db: Session = Depends(get_db)):
    """Обработка вебхука от Альфа-Банка"""
    return await alfa_payment.handle_webhook(db, data)


@router.get("/orders/", response_model=List[schemas.Order])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = crud.get_orders(db, skip=skip, limit=limit)
    return orders


@router.get("/orders/{order_id}", response_model=schemas.Order)
def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = alfa_emulator.get_payment_by_order_id(order_id)

    order_dict = db_order.__dict__
    if payment and payment.get("transaction_id"):
        order_dict["transaction_id"] = payment["transaction_id"]

    return order_dict


@router.get("/settings/", response_model=schemas.Settings)
def get_settings(db: Session = Depends(get_db)):
    return crud.get_settings(db)


@router.get("/azs/nearby", response_model=schemas.AzsWithCoords)
async def get_nearest_azs(lat: float, lon: float, db: Session = Depends(get_db)):
    """Получение ближайшей АЗС по геолокации"""
    try:
        settings = crud.get_settings(db)

        # Получаем список всех АЗС с координатами
        azs_list = price_parser.get_azs_list(use_cache_on_error=True)
        if not azs_list:
            raise HTTPException(
                status_code=404, detail="Не удалось загрузить список АЗС"
            )

        # Находим ближайшую АЗС
        nearest_azs = None
        min_distance = float("inf")

        for azs in azs_list:
            if azs.get("lat") and azs.get("lon"):
                distance = calculate_distance(lat, lon, azs["lat"], azs["lon"])
                if distance < min_distance:
                    min_distance = distance
                    nearest_azs = azs

        if not nearest_azs:
            raise HTTPException(
                status_code=404, detail="В радиусе 50 км не найдено АЗС"
            )

        # Получаем данные с применением скидок
        azs_data = price_parser.get_azs_data_with_discount(
            nearest_azs["number"], settings, nearest_azs["id"]
        )

        if "error" in azs_data:
            raise HTTPException(status_code=404, detail=azs_data["error"])

        azs_data["distance"] = round(min_distance, 2)
        azs_data["lat"] = nearest_azs["lat"]
        azs_data["lon"] = nearest_azs["lon"]

        return azs_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in get_nearest_azs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/azs/{azs_number}/{azs_id}", response_model=schemas.AzsBaseResponse)
async def get_specific_azs(azs_number: int, azs_id: int, db: Session = Depends(get_db)):
    """Получение данных конкретной АЗС по ID"""
    try:
        validate_azs_number(azs_number)
        settings = crud.get_settings(db)

        # Получаем данные с применением скидок, передавая azs_id
        azs_data = price_parser.get_azs_data_with_discount(azs_number, settings, azs_id)
        if "error" in azs_data:
            raise HTTPException(status_code=404, detail=azs_data["error"])

        # Проверяем, что возвращена правильная АЗС
        if azs_data.get("id") != azs_id:
            print(
                f"ВНИМАНИЕ: Запрошена АЗС ID {azs_id}, но возвращена АЗС ID {azs_data.get('id')}"
            )

        # Убеждаемся, что ID установлен правильно
        azs_data["id"] = azs_id

        return azs_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_specific_azs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cache/refresh")
async def refresh_cache(db: Session = Depends(get_db)):
    """Принудительное обновление кэша данных"""
    try:
        price_parser.force_refresh_all_cache()
        return {"status": "success", "message": "Кэш успешно обновлен"}
    except Exception as e:
        print(f"Ошибка при обновлении кэша: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления кэша")


@router.post("/auth/register", response_model=schemas.User)
async def register(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """Регистрация нового пользователя"""
    try:
        user = crud.create_user(db, user_data)
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/auth/login", response_model=schemas.Token)
async def login(
    login_data: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    """Авторизация пользователя"""
    user = crud.authenticate_user(db, login_data.login, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Создаем сессию
    session = crud.create_user_session(db, user.id)

    # Создаем JWT токен
    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/auth/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Выход из системы"""
    success = crud.delete_user_session(db, token)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Successfully logged out"}


@router.get("/auth/me", response_model=schemas.User)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Получение информации о текущем пользователе"""
    user = crud.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Вычисление расстояния между двумя точками в километрах (формула Haversine)"""
    R = 6371  # Радиус Земли в километрах

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c
