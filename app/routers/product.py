from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)
@router.get("/", response_model=List[schemas.ProductResponse])

def get_products(db: Session = Depends(get_db)):
    """
    Lấy toàn bộ sản phẩm
    """
    products = db.query(models.Product).all()
    return products
