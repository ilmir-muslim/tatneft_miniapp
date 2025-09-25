from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware


from .utils.notifications import handle_websocket

from .admin_api import router as admin_router
from .user_api import router as user_router
from .emulator_api import router as emulator_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://admin.toplivo16.ru",
        "https://toplivo16.ru",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(user_router)
app.include_router(admin_router, prefix="/admin")
app.include_router(emulator_router)


@app.get("/")
async def root():
    return {"message": "Tatneft MiniApp API"}


@app.websocket("/admin/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Добавьте проверку origin
    origin = websocket.headers.get("origin")
    allowed_origins = [
        "https://admin.toplivo16.ru",
        "https://toplivo16.ru",
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    if origin not in allowed_origins:
        await websocket.close(code=403)
        return

    await websocket.accept()
    await handle_websocket(websocket)


@app.get("/payment-result")
async def payment_result():
    """Страница результата платежа (для redirect URL)"""
    return {"message": "Платеж обработан"}
