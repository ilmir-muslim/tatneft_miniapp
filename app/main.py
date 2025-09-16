from typing import Optional
from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
from sqlalchemy.orm import Session

from app.utils.price_parser import PriceParser
from . import crud, schemas

from .database import SessionLocal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

price_parser = PriceParser()

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Tatneft MiniApp API"}


@app.post("/orders/", response_model=schemas.Order)
async def create_order(
    user_id: int,
    azs_number: int = Form(...),
    column_number: int = Form(...),
    fuel_type: str = Form(...),
    volume: float = Form(...),
    amount: float = Form(...),
    cheque_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    order_data = schemas.OrderCreate(
        azs_number=azs_number,
        column_number=column_number,
        fuel_type=fuel_type,
        volume=volume,
        amount=amount,
    )

    return await crud.create_order(
        db=db, order=order_data, user_id=user_id, cheque_image=cheque_image
    )


@app.get("/orders/", response_model=list[schemas.Order])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = crud.get_orders(db, skip=skip, limit=limit)
    return orders


@app.get("/orders/{order_id}", response_model=schemas.Order)
def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order


@app.patch("/orders/{order_id}")
def update_order_status(
    order_id: int,
    status: schemas.OrderStatus,
    rejection_reason: str = None,
    db: Session = Depends(get_db),
):
    return crud.update_order_status(db, order_id, status.value, rejection_reason)


@app.get("/settings/", response_model=schemas.Settings)
def get_settings(db: Session = Depends(get_db)):
    return crud.get_settings(db)


@app.put("/settings/", response_model=schemas.Settings)
def update_settings(settings: schemas.SettingsUpdate, db: Session = Depends(get_db)):
    return crud.update_settings(db, settings)


@app.get("/azs/{azs_number}", response_model=schemas.AzsResponse)
def get_azs_data(azs_number: int, db: Session = Depends(get_db)):
    try:
        settings = crud.get_settings(db)
        azs_data = price_parser.get_azs_data_with_discount(azs_number, settings)

        if "error" in azs_data:
            print(f"AZS {azs_number} error: {azs_data['error']}")  # Логирование
            raise HTTPException(status_code=404, detail=azs_data["error"])

        return azs_data
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Логирование неожиданных ошибок
        raise HTTPException(status_code=500, detail="Internal server error")
