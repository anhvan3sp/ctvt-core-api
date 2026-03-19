from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TonKhoChotNgay, SanPham
from app.auth_utils import require_roles

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("")
def inventory(
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin","ke_toan","ke_toan_online"]))
):

    data = (
        db.query(
            SanPham.ten_sp,
            TonKhoChotNgay.so_luong
        )
        .join(SanPham, SanPham.ma_sp == TonKhoChotNgay.ma_sp)
        .all()
    )

    result = []

    for ten_sp, so_luong in data:
        result.append({
            "ten_sp": ten_sp,
            "ton": float(so_luong or 0)
        })

    return result
