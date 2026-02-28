from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import KhachHang
from app.schemas import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/customer", tags=["Customer"])


@router.post("/", response_model=CustomerResponse)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(KhachHang).filter(KhachHang.ma_kh == data.ma_kh).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mã khách hàng đã tồn tại")

    customer = KhachHang(**data.dict())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/", response_model=List[CustomerResponse])
def get_customers(db: Session = Depends(get_db)):
    return db.query(KhachHang).all()
