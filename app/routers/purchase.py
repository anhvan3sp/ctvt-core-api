from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import HoaDonNhapCreate, HoaDonNhapResponse
from app.services import create_hoa_don_nhap
from app.auth_utils import require_roles, get_current_user
from app.models import HoaDonNhap

router = APIRouter(prefix="/purchase", tags=["Purchase"])


@router.post("/")
def create_purchase(
    data: HoaDonNhapCreate,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "nv_dac_biet"]))
):

    # ---- chặn nhân viên Công nhập hàng ----
    if user.ma_nv == "cong":
        raise HTTPException(
            status_code=403,
            detail="Nhan vien Cong khong duoc phep nhap hang"
        )

    # ---- kiểm tra quyền kho ----
    if user.vai_tro != "admin":

        sql = """
        SELECT 1
        FROM nhan_vien_kho
        WHERE ma_nv = :ma_nv
        AND ma_kho = :ma_kho
        """

        row = db.execute(
            sql,
            {
                "ma_nv": user.ma_nv,
                "ma_kho": data.ma_kho
            }
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=403,
                detail="Nhan vien khong duoc phep su dung kho nay"
            )

    return create_hoa_don_nhap(db, data, user)


@router.get("/", response_model=List[HoaDonNhapResponse])
def get_purchase_list(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return db.query(HoaDonNhap).order_by(HoaDonNhap.id.desc()).all()
