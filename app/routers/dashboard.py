from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app.models import (
    QuyCongTyChotNgay,
    QuyNhanVienChotNgay,
    SanPham,
    NhanVien,
    HoaDonBan,
    HoaDonBanChiTiet,
    HoaDonNhap,
    PhatSinh
)
from app.auth_utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# =========================
# TIME VIỆT NAM (NAIVE - MATCH DB)
# =========================
def get_range_today():
    now = datetime.now()  # 🔥 KHÔNG timezone
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


@router.get("")
def dashboard(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    start, end = get_range_today()

    # =========================
    # LẤY TÊN NV
    # =========================
    nv = db.query(NhanVien).filter(
        NhanVien.ma_nv == user.ma_nv
    ).first()

    ten_nv = nv.ten_nv if nv else user.ma_nv

    # =========================
    # BÁN THEO LOẠI (JOIN CHI TIẾT)
    # =========================
    def get_ban_theo_loai(filter_nv):

        rows = db.query(
            SanPham.ten_sp,
            func.coalesce(func.sum(HoaDonBanChiTiet.so_luong), 0)
        ).join(
            HoaDonBan, HoaDonBanChiTiet.id_hoa_don == HoaDonBan.id
        ).join(
            SanPham, HoaDonBanChiTiet.ma_sp == SanPham.ma_sp
        ).filter(
            HoaDonBan.trang_thai == "xac_nhan",
            HoaDonBan.ngay >= start,
            HoaDonBan.ngay < end,
            *filter_nv
        ).group_by(SanPham.ten_sp).all()

        return [
            {
                "ten": r[0],
                "so_luong": float(r[1] or 0)
            } for r in rows if (r[1] or 0) > 0
        ]

    # =========================
    # THU
    # =========================
    def get_thu(filter_nv):

        thu_ban = db.query(
            func.coalesce(func.sum(HoaDonBan.tong_thanh_toan), 0)
        ).filter(
            HoaDonBan.trang_thai == "xac_nhan",
            HoaDonBan.ngay >= start,
            HoaDonBan.ngay < end,
            *filter_nv
        ).scalar() or 0

        thu_ps = db.query(
            func.coalesce(func.sum(PhatSinh.so_tien), 0)
        ).filter(
            PhatSinh.trang_thai == "xac_nhan",
            PhatSinh.loai == "thu",
            PhatSinh.ngay >= start,
            PhatSinh.ngay < end,
            *filter_nv
        ).scalar() or 0

        return float(thu_ban + thu_ps)

    # =========================
    # CHI
    # =========================
    def get_chi(filter_nv):

        chi_nhap = db.query(
            func.coalesce(func.sum(HoaDonNhap.tong_tien), 0)
        ).filter(
            HoaDonNhap.trang_thai == "xac_nhan",
            HoaDonNhap.ngay >= start,
            HoaDonNhap.ngay < end,
            *filter_nv
        ).scalar() or 0

        chi_ps = db.query(
            func.coalesce(func.sum(PhatSinh.so_tien), 0)
        ).filter(
            PhatSinh.trang_thai == "xac_nhan",
            PhatSinh.loai == "chi",
            PhatSinh.ngay >= start,
            PhatSinh.ngay < end,
            *filter_nv
        ).scalar() or 0

        return float(chi_nhap + chi_ps)

    # =========================
    # ADMIN
    # =========================
    if user.ma_nv == "admin":

        ban_theo_loai = get_ban_theo_loai([])
        ban_hom_nay = sum(x["so_luong"] for x in ban_theo_loai)

        thu_tien = get_thu([])
        chi_tien = get_chi([])

        quy = db.query(QuyCongTyChotNgay).first()

        return {
            "loai": "cong_ty",
            "ten_nv": ten_nv,
            "vai_tro": user.vai_tro,

            "ban_hom_nay": float(ban_hom_nay),
            "ban_theo_loai": ban_theo_loai,

            "doanh_thu": float(thu_tien),
            "chi_phi": float(chi_tien),

            "thu_tien": float(thu_tien),
            "chi_tien": float(chi_tien),

            "tien_mat": float(quy.tien_mat) if quy else 0,
            "tien_ngan_hang": float(quy.tien_ngan_hang) if quy else 0,
            "tong_quy": float(quy.tong_quy) if quy else 0
        }

    # =========================
    # NHÂN VIÊN
    # =========================
    else:

        ban_theo_loai = get_ban_theo_loai([
            HoaDonBan.ma_nv == user.ma_nv
        ])

        ban_hom_nay = sum(x["so_luong"] for x in ban_theo_loai)

        thu_tien = get_thu([
            HoaDonBan.ma_nv == user.ma_nv
        ])

        chi_tien = get_chi([
            HoaDonNhap.ma_nv == user.ma_nv
        ])

        quy = db.query(QuyNhanVienChotNgay).filter(
            QuyNhanVienChotNgay.ma_nv == user.ma_nv
        ).first()

        return {
            "loai": "nhan_vien",
            "ten_nv": ten_nv,
            "vai_tro": user.vai_tro,

            "ban_hom_nay": float(ban_hom_nay),
            "ban_theo_loai": ban_theo_loai,

            "doanh_thu": float(thu_tien),
            "chi_phi": float(chi_tien),

            "thu_tien": float(thu_tien),
            "chi_tien": float(chi_tien),

            "so_du": float(quy.so_du) if quy else 0
        }
