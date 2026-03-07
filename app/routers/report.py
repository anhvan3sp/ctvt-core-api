from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from sqlalchemy import func

from app.database import get_db
from app.models import (
    HoaDonBan,
    HoaDonBanChiTiet,
    HoaDonNhap,
    ThuChi,
    KhachHang
)

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/day")
def report_day(ngay: date, db: Session = Depends(get_db)):

    # =========================
    # BÁN HÀNG
    # =========================

    sales = (
        db.query(HoaDonBan, KhachHang.ten_cua_hang)
        .join(KhachHang, HoaDonBan.ma_kh == KhachHang.ma_kh)
        .filter(HoaDonBan.ngay == ngay)
        .all()
    )

    hoa_don_ban = []

    tong_ban = 0
    tong_tien_mat = 0
    tong_tien_ck = 0
    tong_so_binh_ban = 0

    for s, ten_kh in sales:

        # tổng số bình trong hóa đơn
        so_binh = (
            db.query(func.sum(HoaDonBanChiTiet.so_luong))
            .filter(HoaDonBanChiTiet.id_hoa_don == s.id)
            .scalar() or 0
        )

        tong_so_binh_ban += so_binh

        hoa_don_ban.append({
            "so_hd": s.so_hd,
            "ten_kh": ten_kh,
            "so_binh": float(so_binh),
            "tong_tien": float(s.tong_tien or 0),
            "tien_mat": float(s.tien_mat or 0),
            "tien_ck": float(s.tien_ck or 0),
            "tong_thanh_toan": float(s.tong_thanh_toan or 0),
            "ngay": s.ngay
        })

        tong_ban += float(s.tong_thanh_toan or 0)
        tong_tien_mat += float(s.tien_mat or 0)
        tong_tien_ck += float(s.tien_ck or 0)


    # =========================
    # NHẬP HÀNG
    # =========================

    purchases = db.query(HoaDonNhap).filter(HoaDonNhap.ngay == ngay).all()

    hoa_don_nhap = []
    tong_nhap = 0

    for p in purchases:

        hoa_don_nhap.append({
            "so_hd": p.id,
            "tong_tien": float(p.tong_tien or 0),
            "ngay": p.ngay
        })

        tong_nhap += float(p.tong_tien or 0)


    # =========================
    # THU CHI
    # =========================

    thu_chi = (
        db.query(ThuChi)
        .filter(func.date(ThuChi.ngay) == ngay)
        .all()
    )

    thu_chi_trong_ngay = []

    tong_thu = 0
    tong_chi = 0

    for t in thu_chi:

        so_tien = float(t.so_tien or 0)

        thu_chi_trong_ngay.append({
            "doi_tuong": t.doi_tuong,
            "so_tien": so_tien,
            "hinh_thuc": t.hinh_thuc,
            "ngay": t.ngay
        })

        if t.loai == "thu":
            tong_thu += so_tien
        else:
            tong_chi += so_tien


    # =========================
    # TỔNG KẾT
    # =========================

    ton_quy_cuoi_ngay = (
        tong_tien_mat
        + tong_tien_ck
        + tong_thu
        - tong_chi
        - tong_nhap
    )

    return {

        "hoa_don_ban_trong_ngay": hoa_don_ban,

        "hoa_don_nhap_trong_ngay": hoa_don_nhap,

        "thu_chi_trong_ngay": thu_chi_trong_ngay,

        "tong_ket": {

            "tong_so_binh_ban": float(tong_so_binh_ban),

            "tong_ban": tong_ban,

            "tong_nhap": tong_nhap,

            "tong_tien_mat": tong_tien_mat,

            "tong_chuyen_khoan": tong_tien_ck,

            "tong_thu_khac": tong_thu,

            "tong_chi": tong_chi,

            "ton_quy_cuoi_ngay": ton_quy_cuoi_ngay
        }

    }
