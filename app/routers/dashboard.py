from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.database import get_db
from app.models import (
    ThuChi,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    NhatKyKho
)
from app.auth_utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def dashboard(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    today = date.today()

    # ================================
    # SỐ BÌNH BÁN HÔM NAY
    # ================================
    ban_hom_nay = db.query(
        func.coalesce(func.sum(NhatKyKho.so_luong), 0)
    ).filter(
        NhatKyKho.loai == "xuat",
        func.date(NhatKyKho.ngay) == today
    ).scalar()

    # =================================
    # ADMIN → QUỸ CÔNG TY
    # =================================

    if user.ma_nv == "admin":

        quy = (
            db.query(QuyCongTyChotNgay)
            .order_by(QuyCongTyChotNgay.ngay_chot.desc())
            .first()
        )

        tien_mat = float(quy.tien_mat) if quy else 0
        tien_ngan_hang = float(quy.tien_ngan_hang) if quy else 0
        tong_quy = float(quy.tong_quy) if quy else 0

        thu = db.query(func.sum(ThuChi.so_tien)).filter(
            ThuChi.loai == "thu",
            func.date(ThuChi.ngay) == today
        ).scalar() or 0

        chi = db.query(func.sum(ThuChi.so_tien)).filter(
            ThuChi.loai == "chi",
            func.date(ThuChi.ngay) == today
        ).scalar() or 0

        return {
            "loai": "cong_ty",
            "ban_hom_nay": float(ban_hom_nay),
            "tien_mat": float(tien_mat),
            "tien_ngan_hang": float(tien_ngan_hang),
            "tong_quy": float(tong_quy),
            "thu_hom_nay": float(thu),
            "chi_hom_nay": float(chi)
        }

    # =================================
    # NHÂN VIÊN → QUỸ CÁ NHÂN
    # =================================

    else:

        quy = (
            db.query(QuyNhanVienChotNgay)
            .filter(QuyNhanVienChotNgay.ma_nv == user.ma_nv)
            .order_by(QuyNhanVienChotNgay.ngay_chot.desc())
            .first()
        )

        so_du = float(quy.so_du) if quy else 0

        thu = db.query(func.sum(ThuChi.so_tien)).filter(
            ThuChi.ma_nv == user.ma_nv,
            ThuChi.loai == "thu",
            func.date(ThuChi.ngay) == today
        ).scalar() or 0

        chi = db.query(func.sum(ThuChi.so_tien)).filter(
            ThuChi.ma_nv == user.ma_nv,
            ThuChi.loai == "chi",
            func.date(ThuChi.ngay) == today
        ).scalar() or 0

        return {
            "loai": "nhan_vien",
            "ban_hom_nay": float(ban_hom_nay),
            "so_du": float(so_du),
            "thu_hom_nay": float(thu),
            "chi_hom_nay": float(chi)
        }
