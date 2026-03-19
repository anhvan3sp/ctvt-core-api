from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app.models import NhatKyKho, QuyCongTyChotNgay, QuyNhanVienChotNgay
from app.auth_utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    # TIME VN
    now = datetime.utcnow() + timedelta(hours=7)
    start = datetime(now.year, now.month, now.day)
    end = start + timedelta(days=1)

    # =========================
    # ADMIN
    # =========================
    if user.ma_nv == "admin":

        ban_hom_nay = db.query(
            func.coalesce(func.sum(NhatKyKho.so_luong), 0)
        ).filter(
            NhatKyKho.loai == "xuat",
            NhatKyKho.ngay >= start,
            NhatKyKho.ngay < end
        ).scalar() or 0

        # 👉 LẤY QUỸ CÔNG TY (1 dòng)
        quy = db.query(QuyCongTyChotNgay).first()

        tien_mat = float(quy.tien_mat) if quy else 0
        tien_ngan_hang = float(quy.tien_ngan_hang) if quy else 0
        tong_quy = float(quy.tong_quy) if quy else 0

        return {
            "loai": "cong_ty",
            "ban_hom_nay": float(ban_hom_nay),
            "tien_mat": tien_mat,
            "tien_ngan_hang": tien_ngan_hang,
            "tong_quy": tong_quy,
            "thu_hom_nay": 0,
            "chi_hom_nay": 0
        }

    # =========================
    # NHÂN VIÊN
    # =========================
    else:

        ban_hom_nay = db.query(
            func.coalesce(func.sum(NhatKyKho.so_luong), 0)
        ).filter(
            NhatKyKho.loai == "xuat",
            NhatKyKho.ma_nv == user.ma_nv,
            NhatKyKho.ngay >= start,
            NhatKyKho.ngay < end
        ).scalar() or 0

        quy = db.query(QuyNhanVienChotNgay).filter(
            QuyNhanVienChotNgay.ma_nv == user.ma_nv
        ).first()

        so_du = float(quy.so_du) if quy else 0

        return {
            "loai": "nhan_vien",
            "ban_hom_nay": float(ban_hom_nay),
            "so_du": so_du,
            "thu_hom_nay": 0,
            "chi_hom_nay": 0
        }
