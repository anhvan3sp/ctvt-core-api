from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta

from app.database import get_db
from app.models import (
    NhatKyKho,
    QuyCongTyChotNgay,
    QuyNhanVienChotNgay,
    ThuChi,
    SanPham,
    NhanVien,
    HoaDonBan,
    HoaDonNhap,
    PhatSinh
)
from app.auth_utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    now = datetime.utcnow() + timedelta(hours=7)
    start = datetime(now.year, now.month, now.day)
    end = start + timedelta(days=1)

    nv = db.query(NhanVien).filter(
        NhanVien.ma_nv == user.ma_nv
    ).first()

    ten_nv = nv.ten_nv if nv else user.ma_nv

    # =========================
    # BÁN (SỐ BÌNH)
    # =========================
    def get_ban_theo_loai(query_filter):

        rows = db.query(
            SanPham.ten_sp,
            func.sum(
                case(
                    (NhatKyKho.loai == "xuat", NhatKyKho.so_luong),
                    else_=-NhatKyKho.so_luong
                )
            )
        ).join(
            SanPham, NhatKyKho.ma_sp == SanPham.ma_sp
        ).filter(
            NhatKyKho.ngay >= start,
            NhatKyKho.ngay < end,
            *query_filter
        ).group_by(SanPham.ten_sp).all()

        return [
            {
                "ten": r[0],
                "so_luong": float(r[1] or 0)
            } for r in rows if (r[1] or 0) > 0
        ]

    # =========================
    # DOANH THU (🔥 từ hoá đơn)
    # =========================
    def get_doanh_thu(filter_nv):

        return db.query(
            func.coalesce(func.sum(HoaDonBan.tong_thanh_toan), 0)
        ).filter(
            HoaDonBan.trang_thai == "xac_nhan",
            HoaDonBan.ngay >= start,
            HoaDonBan.ngay < end,
            *filter_nv
        ).scalar() or 0

    # =========================
    # CHI PHÍ (🔥 nhập + phát sinh)
    # =========================
    def get_chi_phi(filter_nv):

        nhap = db.query(
            func.coalesce(func.sum(HoaDonNhap.tong_tien), 0)
        ).filter(
            HoaDonNhap.trang_thai == "xac_nhan",
            HoaDonNhap.ngay >= start,
            HoaDonNhap.ngay < end,
            *filter_nv
        ).scalar() or 0

        phat_sinh = db.query(
            func.coalesce(func.sum(PhatSinh.so_tien), 0)
        ).filter(
            PhatSinh.trang_thai == "xac_nhan",
            PhatSinh.loai == "chi",
            PhatSinh.ngay >= start,
            PhatSinh.ngay < end,
            *filter_nv
        ).scalar() or 0

        return float(nhap + phat_sinh)

    # =========================
    # DÒNG TIỀN (ledger)
    # =========================
    def get_cashflow(filter_nv):

        thu = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
            ThuChi.loai == "thu",
            ThuChi.ngay >= start,
            ThuChi.ngay < end,
            *filter_nv
        ).scalar() or 0

        chi = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
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

        doanh_thu = get_doanh_thu([])
        chi_phi = get_chi_phi([])

        thu_tien, chi_tien = get_cashflow([])

        quy = db.query(QuyCongTyChotNgay).first()

        tien_mat = float(quy.tien_mat) if quy else 0
        tien_ngan_hang = float(quy.tien_ngan_hang) if quy else 0
        tong_quy = float(quy.tong_quy) if quy else 0

        return {
            "loai": "cong_ty",
            "ten_nv": ten_nv,
            "vai_tro": user.vai_tro,

            "ban_hom_nay": float(ban_hom_nay),
            "ban_theo_loai": ban_theo_loai,

            # 🔥 chuẩn tài chính
            "doanh_thu": float(doanh_thu),
            "chi_phi": float(chi_phi),

            # 🔥 dòng tiền
            "thu_tien": thu_tien,
            "chi_tien": chi_tien,

            "tien_mat": tien_mat,
            "tien_ngan_hang": tien_ngan_hang,
            "tong_quy": tong_quy
        }

    # =========================
    # NHÂN VIÊN
    # =========================
    else:

        ban_theo_loai = get_ban_theo_loai([
            NhatKyKho.ma_nv == user.ma_nv
        ])

        ban_hom_nay = sum(x["so_luong"] for x in ban_theo_loai)

        doanh_thu = get_doanh_thu([
            HoaDonBan.ma_nv == user.ma_nv
        ])

        chi_phi = get_chi_phi([
            HoaDonNhap.ma_nv == user.ma_nv
        ])

        thu_tien, chi_tien = get_cashflow([
            ThuChi.ma_nv == user.ma_nv
        ])

        quy = db.query(QuyNhanVienChotNgay).filter(
            QuyNhanVienChotNgay.ma_nv == user.ma_nv
        ).first()

        so_du = float(quy.so_du) if quy else 0

        return {
            "loai": "nhan_vien",
            "ten_nv": ten_nv,
            "vai_tro": user.vai_tro,

            "ban_hom_nay": float(ban_hom_nay),
            "ban_theo_loai": ban_theo_loai,

            "doanh_thu": float(doanh_thu),
            "chi_phi": float(chi_phi),

            "thu_tien": thu_tien,
            "chi_tien": chi_tien,

            "so_du": so_du
        }
