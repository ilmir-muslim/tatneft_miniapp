import asyncio
import random
from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import crud, models


class AlfaPaymentEmulator:
    """Эмулятор API Альфа-Банка для тестирования"""

    def __init__(self):
        self.payments = {}
        self.success_rate = 0.8  # 80% успешных платежей

    async def create_payment(
        self, db: Session, order, return_url: str
    ) -> Dict[str, Any]:
        """Создание эмулированного платежа"""

        # Генерируем ID платежа
        payment_id = f"emulator_{order.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Сохраняем информацию о платеже
        self.payments[payment_id] = {
            "order_id": order.id,
            "amount": order.amount or (order.volume * order.fuel_price),
            "status": "created",
            "created_at": datetime.now(),
            "return_url": return_url,
            "order_data": {
                "azs_number": order.azs_number,
                "column_number": order.column_number,
                "fuel_type": order.fuel_type,
                "fuel_price": order.fuel_price,
                "volume": order.volume,
                "amount": order.amount,
                "user_id": order.user_id,
            },
        }

        # Эмулируем задержку API
        await asyncio.sleep(1)

        # Генерируем URL для эмулированного банковского интерфейса
        # Используем абсолютный URL для корректной работы в мини-приложении
        base_url = "http://localhost:8001"  # Можно вынести в настройки
        payment_url = f"{base_url}/payment-emulator/{payment_id}"

        return {"formUrl": payment_url, "orderId": payment_id, "payment_id": payment_id}

    async def process_payment(self, payment_id: str, action: str) -> Dict[str, Any]:
        """Обработка платежа в эмуляторе"""

        if payment_id not in self.payments:
            raise HTTPException(status_code=404, detail="Payment not found")

        payment = self.payments[payment_id]

        # Эмулируем обработку платежа
        await asyncio.sleep(2)

        if action == "success":
            # Имитируем успешный платеж
            if random.random() < self.success_rate:
                payment["status"] = "COMPLETED"
                payment["completed_at"] = datetime.now()
                payment["transaction_id"] = (
                    f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
                )
                result = {
                    "status": "COMPLETED",
                    "message": "Платеж успешно завершен",
                    "transaction_id": payment["transaction_id"],
                }
            else:
                # Имитируем случайный отказ
                failure_reasons = [
                    "Недостаточно средств",
                    "Превышен лимит операции",
                    "Карта заблокирована",
                    "Ошибка связи с банком-эмитентом",
                ]
                payment["status"] = "DECLINED"
                payment["failure_reason"] = random.choice(failure_reasons)
                result = {"status": "DECLINED", "message": payment["failure_reason"]}
        elif action == "fail":
            # Принудительный отказ
            payment["status"] = "DECLINED"
            payment["failure_reason"] = "Платеж отклонен по инициативе пользователя"
            result = {"status": "DECLINED", "message": payment["failure_reason"]}
        else:
            # Пользователь отменил платеж
            payment["status"] = "CANCELLED"
            result = {"status": "CANCELLED", "message": "Платеж отменен пользователем"}

        return result

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Получение статуса платежа"""

        if payment_id not in self.payments:
            raise HTTPException(status_code=404, detail="Payment not found")

        return self.payments[payment_id]

    async def handle_webhook(self, db: Session, data: dict):
        """Эмулятор вебхука - в реальной реализации будет вызываться банком"""

        payment_id = data.get("orderId")
        status = data.get("status")

        if payment_id not in self.payments:
            return {"status": "error", "message": "Payment not found"}

        payment = self.payments[payment_id]
        order_id = payment["order_id"]

        # Обновляем статус заказа в базе
        if status == "COMPLETED":
            crud.update_order_status(db, order_id, "принято")
            crud.update_order_payment_status(db, order_id, "succeeded")
        elif status == "DECLINED":
            reason = data.get("reason", "Платеж отклонен банком")
            crud.update_order_status(db, order_id, "отказано", reason)
            crud.update_order_payment_status(db, order_id, "failed")
        elif status == "CANCELLED":
            crud.update_order_status(
                db, order_id, "отказано", "Платеж отменен пользователем"
            )
            crud.update_order_payment_status(db, order_id, "canceled")

        return {"status": "ok"}

    def get_payment_by_order_id(self, order_id: int) -> Dict[str, Any]:
        """Поиск платежа по ID заказа"""
        for payment_id, payment in self.payments.items():
            if payment.get("order_id") == order_id:
                return payment
        return None


# Глобальный экземпляр эмулятора
alfa_emulator = AlfaPaymentEmulator()

