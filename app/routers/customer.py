from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import KhachHang
from app.schemas import CustomerCreate, CustomerResponse
from sqlalchemy import func
from app.models import HoaDonBan
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

@router.get("/debt/{ma_kh}")
def get_customer_debt(ma_kh: str, db: Session = Depends(get_db)):

    tong_no = db.query(
        func.coalesce(func.sum(HoaDonBan.no_lai), 0)
    ).filter(
        HoaDonBan.ma_kh == ma_kh
    ).scalar()

    return {
        "ma_kh": ma_kh,
        "tong_cong_no": tong_no
    }
