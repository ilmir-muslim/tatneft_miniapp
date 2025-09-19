from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .utils.notifications import handle_websocket

from .admin_api import router as admin_router
from .user_api import router as user_router

Path("uploads").mkdir(exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(admin_router, prefix="/admin")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def root():
    return {"message": "Tatneft MiniApp API"}


@app.websocket("/admin/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket(websocket)
