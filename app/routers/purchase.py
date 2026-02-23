from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import HoaDonNhapCreate, HoaDonNhapResponse
from app.services import create_hoa_don_nhap
from app.auth_utils import get_current_user
from app.models import HoaDonNhap

router = APIRouter(prefix="/purchase", tags=["Purchase"])


@router.post("/", response_model=HoaDonNhapResponse)
def create_purchase(
    data: HoaDonNhapCreate,
    db: Session = Depends(get_db),
    ma_nv: str = Depends(get_current_user)
):
    try:
        hoa_don = create_hoa_don_nhap(db, data, ma_nv)
        return hoa_don
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[HoaDonNhapResponse])
def get_purchase_list(
    db: Session = Depends(get_db),
    ma_nv: str = Depends(get_current_user)
):
    return db.query(HoaDonNhap).order_by(HoaDonNhap.id.desc()).all()
