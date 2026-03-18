from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.database import get_db
from app.schemas import HoaDonBanCreate
from app.services import create_hoa_don_ban, get_sale_detail
from app.auth_utils import require_roles
from app.models import HoaDonBan

router = APIRouter(prefix="/sale", tags=["Sale"])


@router.post("/")
def create_sale(
    data: HoaDonBanCreate,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "nv_dac_biet"]))
):

    # kiểm tra quyền kho
    if user.vai_tro != "admin":

        sql = text("""
        SELECT 1
        FROM nhan_vien_kho
        WHERE ma_nv = :ma_nv
        AND ma_kho = :ma_kho
        """)

        row = db.execute(
            sql,
            {"ma_nv": user.ma_nv, "ma_kho": data.ma_kho}
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=403,
                detail="Nhan vien khong duoc phep su dung kho nay"
            )

    # kiểm tra hóa đơn trùng trong ngày
    duplicate = db.query(HoaDonBan).filter(
        HoaDonBan.ma_nv == user.ma_nv,
        HoaDonBan.ma_kh == data.ma_kh,
        HoaDonBan.ma_kho == data.ma_kho,
        func.date(HoaDonBan.ngay) == func.current_date()
    ).first()

    if duplicate and not getattr(data, "force_create", False):
        return {
            "warning": True,
            "message": "Hoa don ban nay co ve da tao trong ngay. Ban co muon tao tiep khong?"
        }

    return create_hoa_don_ban(db, data, user)


@router.get("/detail/{id}")
def sale_detail(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "nv_dac_biet", "ke_toan"]))
):
    return get_sale_detail(db, id)
