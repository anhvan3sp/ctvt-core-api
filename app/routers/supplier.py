from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"]
)

@router.get("/", response_model=List[schemas.Supplier])
def get_suppliers(db: Session = Depends(get_db)):
    """
    Lấy toàn bộ nhà cung cấp
    Dùng cho dropdown frontend
    """
    suppliers = db.query(models.Supplier).all()
    return suppliers
