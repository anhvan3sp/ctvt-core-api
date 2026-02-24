from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.database import get_db
from app.models import NhatKyKho

router = APIRouter(prefix="/stock", tags=["Stock"])

@router.get("/{ma_kho}/{ma_sp}")
def get_stock(ma_kho: str, ma_sp: str, db: Session = Depends(get_db)):

    tong_nhap = db.query(func.coalesce(func.sum(NhatKyKho.so_luong), 0)).filter(
        NhatKyKho.ma_sp == ma_sp,
        NhatKyKho.ma_kho == ma_kho,
        NhatKyKho.loai == "nhap"
    ).scalar()

    tong_xuat = db.query(func.coalesce(func.sum(NhatKyKho.so_luong), 0)).filter(
        NhatKyKho.ma_sp == ma_sp,
        NhatKyKho.ma_kho == ma_kho,
        NhatKyKho.loai == "xuat"
    ).scalar()

    return {
        "ma_kho": ma_kho,
        "ma_sp": ma_sp,
        "ton_kho": Decimal(str(tong_nhap)) - Decimal(str(tong_xuat))
    }
