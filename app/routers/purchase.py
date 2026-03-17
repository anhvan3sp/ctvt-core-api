from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
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

        sql = text("""
        SELECT 1
        FROM nhan_vien_kho
        WHERE ma_nv = :ma_nv
        AND ma_kho = :ma_kho
        """)

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

    # ---- kiểm tra hóa đơn trùng trong ngày ----
    duplicate = db.query(HoaDonNhap).filter(
        HoaDonNhap.ma_nv == user.ma_nv,
        HoaDonNhap.ma_ncc == data.ma_ncc,
        HoaDonNhap.ma_kho == data.ma_kho,
        func.date(HoaDonNhap.ngay) == func.current_date()
    ).first()

    # ---- nếu trùng và chưa xác nhận force_create ----
    if duplicate and not data.force_create:
        return {
            "warning": True,
            "message": "Hoa don nay co ve da nhap trong ngay. Ban co muon nhap tiep khong?"
        }

    # ---- tạo hóa đơn ----
    return create_hoa_don_nhap(db, data, user)


@router.get("/", response_model=List[HoaDonNhapResponse])
def get_purchase_list(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return db.query(HoaDonNhap).order_by(HoaDonNhap.id.desc()).all()
