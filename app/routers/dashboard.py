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

    # =====================================================
    # ADMIN → TOÀN CÔNG TY
    # =====================================================
    if user.ma_nv == "admin":

        # -------- BÁN HÔM NAY (toàn công ty) --------
        ban_hom_nay = db.query(
            func.coalesce(func.sum(NhatKyKho.so_luong), 0)
        ).filter(
            NhatKyKho.loai == "xuat",
            func.date(NhatKyKho.ngay) == today
        ).scalar()

        # -------- QUỸ CÔNG TY --------
        quy = (
            db.query(QuyCongTyChotNgay)
            .order_by(QuyCongTyChotNgay.ngay_chot.desc())
            .first()
        )

        tien_mat = float(quy.tien_mat) if quy else 0
        tien_ngan_hang = float(quy.tien_ngan_hang) if quy else 0
        tong_quy = float(quy.tong_quy) if quy else 0

        # -------- THU CHI HÔM NAY --------
        thu = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
            ThuChi.loai == "thu",
            func.date(ThuChi.ngay) == today
        ).scalar()

        chi = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
            ThuChi.loai == "chi",
            func.date(ThuChi.ngay) == today
        ).scalar()

        return {
            "loai": "cong_ty",
            "ban_hom_nay": float(ban_hom_nay),
            "tien_mat": tien_mat,
            "tien_ngan_hang": tien_ngan_hang,
            "tong_quy": tong_quy,
            "thu_hom_nay": float(thu),
            "chi_hom_nay": float(chi)
        }

    # =====================================================
    # NHÂN VIÊN → CHỈ DATA CỦA MÌNH
    # =====================================================
    else:

        # -------- BÁN HÔM NAY THEO NHÂN VIÊN --------
        ban_hom_nay = db.query(
            func.coalesce(func.sum(NhatKyKho.so_luong), 0)
        ).filter(
            NhatKyKho.loai == "xuat",
            NhatKyKho.ma_nv == user.ma_nv,
            func.date(NhatKyKho.ngay) == today
        ).scalar()

        # -------- QUỸ NHÂN VIÊN --------
        quy = (
            db.query(QuyNhanVienChotNgay)
            .filter(QuyNhanVienChotNgay.ma_nv == user.ma_nv)
            .order_by(QuyNhanVienChotNgay.ngay_chot.desc())
            .first()
        )

        so_du = float(quy.so_du) if quy else 0

        # -------- THU CHI HÔM NAY --------
        thu = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
            ThuChi.ma_nv == user.ma_nv,
            ThuChi.loai == "thu",
            func.date(ThuChi.ngay) == today
        ).scalar()

        chi = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
            ThuChi.ma_nv == user.ma_nv,
            ThuChi.loai == "chi",
            func.date(ThuChi.ngay) == today
        ).scalar()

        return {
            "loai": "nhan_vien",
            "ban_hom_nay": float(ban_hom_nay),
            "so_du": so_du,
            "thu_hom_nay": float(thu),
            "chi_hom_nay": float(chi)
        }
