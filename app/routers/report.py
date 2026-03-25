from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, datetime, time
from sqlalchemy import func

from app.database import get_db
from app.models import (
    HoaDonBan,
    HoaDonBanChiTiet,
    HoaDonNhap,
    ThuChi,
    KhachHang
)
from app.auth_utils import get_current_user

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/day")
def report_day(
    ngay: date | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if ngay is None:
        ngay = date.today()

    start = datetime.combine(ngay, time.min)
    end = datetime.combine(ngay, time.max)

    ma_nv = user.ma_nv

    # =========================
    # MAP LOẠI GIAO DỊCH → NỘI DUNG
    # =========================

    def map_noi_dung(loai_giao_dich):
        mapping = {
            "ban_hang": "Thu bán hàng",
            "nhap_hang": "Chi nhập hàng",
            "do_dau": "Chi đổ dầu",
            "nop_tien": "Nộp tiền",
        }
        return mapping.get(loai_giao_dich, "Khác")

    # =========================
    # BÁN HÀNG
    # =========================

    sales = (
        db.query(HoaDonBan, KhachHang.ten_cua_hang)
        .outerjoin(KhachHang, HoaDonBan.ma_kh == KhachHang.ma_kh)
        .filter(
            HoaDonBan.ngay == ngay,
            HoaDonBan.trang_thai == "xac_nhan",
            HoaDonBan.ma_nv == ma_nv
        )
        .all()
    )

    hoa_don_ban = []

    tong_ban = 0
    tong_tien_mat = 0
    tong_tien_ck = 0
    tong_so_binh_ban = 0

    for s, ten_kh in sales:

        so_binh = (
            db.query(func.sum(HoaDonBanChiTiet.so_luong))
            .filter(HoaDonBanChiTiet.id_hoa_don == s.id)
            .scalar()
        ) or 0

        tong_so_binh_ban += float(so_binh)

        tong_ban += float(s.tong_thanh_toan or 0)
        tong_tien_mat += float(s.tien_mat or 0)
        tong_tien_ck += float(s.tien_ck or 0)

        hoa_don_ban.append({
            "so_hd": s.so_hd,
            "ten_kh": ten_kh or "",
            "so_binh": float(so_binh),
            "tong_tien": float(s.tong_tien or 0),
            "tien_mat": float(s.tien_mat or 0),
            "tien_ck": float(s.tien_ck or 0),
            "tong_thanh_toan": float(s.tong_thanh_toan or 0),
            "ngay": s.ngay
        })


    # =========================
    # NHẬP HÀNG
    # =========================

    purchases = (
        db.query(HoaDonNhap)
        .filter(
            HoaDonNhap.ngay == ngay,
            HoaDonNhap.trang_thai == "xac_nhan",
            HoaDonNhap.ma_nv == ma_nv
        )
        .all()
    )

    hoa_don_nhap = []
    tong_nhap = 0

    for p in purchases:

        tong_nhap += float(p.tong_tien or 0)

        hoa_don_nhap.append({
            "so_hd": p.id,
            "tong_tien": float(p.tong_tien or 0),
            "ngay": p.ngay
        })


    # =========================
    # THU CHI
    # =========================

    thu_chi_data = (
        db.query(ThuChi)
        .filter(
            ThuChi.ngay >= start,
            ThuChi.ngay <= end,
            ThuChi.ma_nv == ma_nv
        )
        .all()
    )

    thu_chi_trong_ngay = []

    tong_thu = 0
    tong_chi = 0

    for t in thu_chi_data:

        so_tien = float(t.so_tien or 0)

        # 🔥 FIX NỘI DUNG
        noi_dung = t.noi_dung if t.noi_dung else map_noi_dung(t.loai_giao_dich)

        thu_chi_trong_ngay.append({
            "doi_tuong": t.doi_tuong,
            "so_tien": so_tien,
            "hinh_thuc": t.hinh_thuc,
            "noi_dung": noi_dung,
            "loai": t.loai,
            "loai_giao_dich": t.loai_giao_dich,
            "ngay": t.ngay
        })

        if t.loai == "thu":
            tong_thu += so_tien
        else:
            tong_chi += so_tien


    # =========================
    # TỔNG KẾT
    # =========================

    ton_quy = (
        tong_tien_mat
        + tong_tien_ck
        + tong_thu
        - tong_chi
        - tong_nhap
    )

    return {

        "nhan_vien": ma_nv,

        "hoa_don_ban_trong_ngay": hoa_don_ban,

        "hoa_don_nhap_trong_ngay": hoa_don_nhap,

        "thu_chi_trong_ngay": thu_chi_trong_ngay,

        "tong_ket": {

            "tong_so_binh_ban": tong_so_binh_ban,

            "tong_ban": tong_ban,

            "tong_nhap": tong_nhap,

            "tong_tien_mat": tong_tien_mat,

            "tong_chuyen_khoan": tong_tien_ck,

            "tong_thu": tong_thu,

            "tong_chi": tong_chi,

            "ton_quy": ton_quy
        }

    }
