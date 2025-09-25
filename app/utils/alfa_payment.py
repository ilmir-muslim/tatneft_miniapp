import aiohttp
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import crud, models
from .alfa_payment_emulator import alfa_emulator


class AlfaPayment:
    def __init__(self):
        self.api_url = "https://partner.alfabank.ru/public-api/v2"
        self.auth_token = None
        self.token_expires = None
        self.use_emulator = (
            True  # Флаг для переключения между эмулятором и реальным API
        )

    async def get_auth_token(self, db: Session):
        """Получение токена аутентификации"""

        # Если используем эмулятор, возвращаем заглушку
        if self.use_emulator:
            return "emulator_token"

        # Реальная логика для работы с API банка
        settings = crud.get_settings(db)

        if not settings.alfa_login or not settings.alfa_password:
            raise HTTPException(
                status_code=500, detail="Не настроены учетные данные API Альфа-Банка"
            )

        return settings.alfa_password

    async def create_payment(self, db: Session, order, return_url: str):
        """Создание платежа - переключается между эмулятором и реальным API"""

        if self.use_emulator:
            # Используем эмулятор
            return await alfa_emulator.create_payment(db, order, return_url)
        else:
            # Реальная логика API банка
            return await self._create_real_payment(db, order, return_url)

    async def _create_real_payment(self, db: Session, order, return_url: str):
        """Реальное создание платежа через API Альфа-Банка"""
        api_key = await self.get_auth_token(db)

        payment_data = {
            "amount": (
                int(order.amount * 100)
                if order.amount
                else int(order.volume * order.fuel_price * 100)
            ),
            "currency": "RUB",
            "orderNumber": str(order.id),
            "returnUrl": return_url,
            "description": f"Оплата топлива на АЗС {order.azs_number}, колонка {order.column_number}",
            "clientId": str(order.user_id),
        }

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "API-key": api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/payments",
                    json=payment_data,
                    headers=headers,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "formUrl": result.get("formUrl"),
                            "orderId": result.get("orderId"),
                        }
                    else:
                        error_text = await response.text()
                        print(f"Payment creation failed: {error_text}")
                        raise Exception(f"Payment creation failed: {error_text}")
        except Exception as e:
            print(f"Error in create_payment: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка создания платежа: {str(e)}"
            )

    async def get_order_status(self, db: Session, order_id: str):
        """Проверка статуса заявки"""

        if self.use_emulator:
            # Используем эмулятор
            return await alfa_emulator.get_payment_status(order_id)
        else:
            # Реальная логика API банка
            return await self._get_real_order_status(db, order_id)

    async def _get_real_order_status(self, db: Session, order_id: str):
        """Реальная проверка статуса через API банка"""
        api_key = await self.get_auth_token(db)

        headers = {"Accept": "application/json; charset=UTF-8", "API-key": api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/leads/{order_id}", headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    raise Exception(f"Status check failed: {await response.text()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Status check error: {str(e)}")

    async def handle_webhook(self, db: Session, data: dict):
        """Обработка вебхука от Альфа-Банка"""

        if self.use_emulator:
            # Используем эмулятор
            return await alfa_emulator.handle_webhook(db, data)
        else:
            # Реальная логика обработки вебхука
            return await self._handle_real_webhook(db, data)

    async def _handle_real_webhook(self, db: Session, data: dict):
        """Реальная обработка вебхука от банка"""
        order_id = data.get("orderId")
        status = data.get("status")

        order = (
            db.query(models.Order).filter(models.Order.payment_id == order_id).first()
        )
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if status == "COMPLETED":
            crud.update_order_status(db, order.id, "принято")
            crud.update_order_payment_status(db, order.id, "succeeded")
        elif status == "DECLINED":
            crud.update_order_status(db, order.id, "отказано", "Платеж отклонен банком")
            crud.update_order_payment_status(db, order.id, "failed")

        return {"status": "ok"}

    def set_mode(self, use_emulator: bool):
        """Переключение между эмулятором и реальным API"""
        self.use_emulator = use_emulator


# Глобальный экземпляр с эмулятором по умолчанию
alfa_payment = AlfaPayment()
