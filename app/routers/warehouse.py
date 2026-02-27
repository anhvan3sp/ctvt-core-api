from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/warehouses",
    tags=["Warehouses"]
)
@router.get("/", response_model=List[schemas.WarehouseResponse])

def get_warehouses(db: Session = Depends(get_db)):
    """
    Lấy toàn bộ kho
    """
    warehouses = db.query(models.Warehouse).all()
    return warehouses
