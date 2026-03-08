from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import NhatKyKho, SanPham
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
            func.sum(NhatKyKho.so_luong).label("ton")
        )
        .join(SanPham, SanPham.ma_sp == NhatKyKho.ma_sp)
        .group_by(SanPham.ten_sp)
        .all()
    )

    result = []

    for ten_sp, ton in data:
        result.append({
            "ten_sp": ten_sp,
            "ton": float(ton or 0)
        })

    return result
