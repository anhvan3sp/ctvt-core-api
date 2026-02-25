from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import HoaDonNhapCreate, HoaDonNhapResponse
from app.services import create_hoa_don_nhap
from app.auth_utils import get_current_user
from app.models import HoaDonNhap
from app.auth_utils import require_roles
router = APIRouter(prefix="/purchase", tags=["Purchase"])



@router.post("/")
def create_purchase(
    data: HoaDonNhapCreate,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "nv_dac_biet"]))
):
    return create_hoa_don_nhap(db, data, user.ma_nv)

@router.get("/", response_model=List[HoaDonNhapResponse])
def get_purchase_list(
    db: Session = Depends(get_db),
    ma_nv: str = Depends(get_current_user)
):
    return db.query(HoaDonNhap).order_by(HoaDonNhap.id.desc()).all()
