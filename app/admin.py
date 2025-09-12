from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import crud, models, schemas
from .database import SessionLocal, engine
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/admin/", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    orders = crud.get_orders(db, skip=0, limit=100)
    return templates.TemplateResponse(
        "admin.html", {"request": request, "orders": orders}
    )


@router.get("/admin/orders/", response_model=List[schemas.Order])
def get_all_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_orders(db, skip=skip, limit=limit)


@router.get("/admin/orders/{order_id}", response_model=schemas.Order)
def get_order_details(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order


@router.post("/admin/orders/{order_id}/accept")
def accept_order(order_id: int, db: Session = Depends(get_db)):
    return crud.update_order_status(db, order_id, "принято")


@router.post("/admin/orders/{order_id}/reject")
def reject_order(order_id: int, reason: str, db: Session = Depends(get_db)):
    return crud.update_order_status(db, order_id, "отказано", reason)
