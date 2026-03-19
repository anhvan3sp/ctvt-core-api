from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TonKhoChotNgay

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/{ma_kho}/{ma_sp}")
def get_stock(ma_kho: str, ma_sp: str, db: Session = Depends(get_db)):

    ton = db.query(TonKhoChotNgay).filter(
        TonKhoChotNgay.ma_kho == ma_kho,
        TonKhoChotNgay.ma_sp == ma_sp
    ).first()

    if not ton:
        raise HTTPException(404, "Không có tồn kho")

    return {
        "ma_kho": ma_kho,
        "ma_sp": ma_sp,
        "ton_kho": float(ton.so_luong or 0)
    }
