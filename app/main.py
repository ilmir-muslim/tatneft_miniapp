from typing import Optional
from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .price_parser import PriceParser
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
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


@app.get("/azs/{azs_number}/prices", response_model=schemas.FuelPricesResponse)
def get_azs_prices(azs_number: int, db: Session = Depends(get_db)):
    """
    Получение актуальных цен на топливо для указанной АЗС
    """
    prices = price_parser.get_prices(db, azs_number)

    if "error" in prices:
        return schemas.FuelPricesResponse(success=False, error=prices["error"])

    return schemas.FuelPricesResponse(success=True, prices=prices)
