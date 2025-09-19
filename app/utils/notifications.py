from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Новое подключение. Всего подключений: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"Отключение. Осталось подключений: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Ошибка broadcast: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


# Глобальный экземпляр менеджера соединений
manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Ожидаем сообщения от клиента (можем использовать для heartbeat)
            data = await websocket.receive_text()
            # Можно обрабатывать разные типы сообщений от клиента
            message = json.loads(data)
            if message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}), websocket
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Ошибка в WebSocket соединении: {e}")
        manager.disconnect(websocket)


async def notify_new_order(order_data):
    """Уведомление о новом заказе"""
    message = json.dumps({"type": "new_order", "data": order_data})
    await manager.broadcast(message)


async def notify_order_update(order_id, status, reason=None):
    """Уведомление об изменении статуса заказа"""
    message = json.dumps(
        {
            "type": "order_update",
            "data": {"order_id": order_id, "status": status, "reason": reason},
        }
    )
    await manager.broadcast(message)
