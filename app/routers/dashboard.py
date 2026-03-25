from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app.models import (
    NhatKyKho,
    QuyCongTyChotNgay,
    QuyNhanVienChotNgay,
    ThuChi,
    SanPham
)
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
    # PHÂN LOẠI BÁN THEO SẢN PHẨM
    # =========================

    def get_ban_theo_loai(query_filter):

        rows = db.query(
            SanPham.ten_sp,
            func.sum(NhatKyKho.so_luong)
        ).join(
            SanPham, NhatKyKho.ma_sp == SanPham.ma_sp
        ).filter(
            NhatKyKho.loai == "xuat",
            NhatKyKho.ngay >= start,
            NhatKyKho.ngay < end,
            *query_filter
        ).group_by(SanPham.ten_sp).all()

        return [
            {
                "ten": r[0],
                "so_luong": float(r[1] or 0)
            } for r in rows
        ]

    # =========================
    # THU / CHI TRONG NGÀY
    # =========================

    def get_thu_chi(filter_nv):

        thu = db.query(
            func.coalesce(func.sum(ThuChi.so_tien), 0)
        ).filter(
            ThuChi.loai == "thu",
            ThuChi.ngay >= start,
            ThuChi.ngay < end,
            *filter_nv
        ).scalar() or 0

        chi = db.query(
            func.coalesce(func.sum(ThuChi.so_tien), 0)
        ).filter(
            ThuChi.loai == "chi",
            ThuChi.ngay >= start,
            ThuChi.ngay < end,
            *filter_nv
        ).scalar() or 0

        return float(thu), float(chi)

    # =========================
    # ADMIN
    # =========================
    if user.ma_nv == "admin":

        ban_theo_loai = get_ban_theo_loai([])

        ban_hom_nay = sum(x["so_luong"] for x in ban_theo_loai)

        thu, chi = get_thu_chi([])

        quy = db.query(QuyCongTyChotNgay).first()

        tien_mat = float(quy.tien_mat) if quy else 0
        tien_ngan_hang = float(quy.tien_ngan_hang) if quy else 0
        tong_quy = float(quy.tong_quy) if quy else 0

        return {
            "loai": "cong_ty",
            "ten_nv": user.ma_nv,
            "ban_hom_nay": float(ban_hom_nay),
            "ban_theo_loai": ban_theo_loai,
            "tien_mat": tien_mat,
            "tien_ngan_hang": tien_ngan_hang,
            "tong_quy": tong_quy,
            "thu_hom_nay": thu,
            "chi_hom_nay": chi
        }

    # =========================
    # NHÂN VIÊN
    # =========================
    else:

        ban_theo_loai = get_ban_theo_loai([
            NhatKyKho.ma_nv == user.ma_nv
        ])

        ban_hom_nay = sum(x["so_luong"] for x in ban_theo_loai)

        thu, chi = get_thu_chi([
            ThuChi.ma_nv == user.ma_nv
        ])

        quy = db.query(QuyNhanVienChotNgay).filter(
            QuyNhanVienChotNgay.ma_nv == user.ma_nv
        ).first()

        so_du = float(quy.so_du) if quy else 0

        return {
            "loai": "nhan_vien",
            "ten_nv": user.ma_nv,
            "ban_hom_nay": float(ban_hom_nay),
            "ban_theo_loai": ban_theo_loai,
            "so_du": so_du,
            "thu_hom_nay": thu,
            "chi_hom_nay": chi
        }
