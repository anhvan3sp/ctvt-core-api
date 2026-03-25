from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, datetime, time
from sqlalchemy import func, and_

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

    is_admin = user.vai_tro == "admin"

    # =========================
    # FILTER NHÂN VIÊN
    # =========================

    def filter_nv(query, model):
        if is_admin:
            return query
        return query.filter(model.ma_nv == user.ma_nv)

    # =========================
    # BÁN HÀNG
    # =========================

    sales_query = (
        db.query(HoaDonBan, KhachHang.ten_cua_hang)
        .outerjoin(KhachHang, HoaDonBan.ma_kh == KhachHang.ma_kh)
        .filter(
            HoaDonBan.ngay == ngay,
            HoaDonBan.trang_thai == "xac_nhan"
        )
    )

    sales_query = filter_nv(sales_query, HoaDonBan)

    sales = sales_query.all()

    tong_ban = 0
    tong_tien_mat = 0
    tong_tien_ck = 0
    tong_so_binh_ban = 0

    for s, _ in sales:

        so_binh = (
            db.query(func.sum(HoaDonBanChiTiet.so_luong))
            .filter(HoaDonBanChiTiet.id_hoa_don == s.id)
            .scalar()
        ) or 0

        tong_so_binh_ban += float(so_binh)
        tong_ban += float(s.tong_thanh_toan or 0)
        tong_tien_mat += float(s.tien_mat or 0)
        tong_tien_ck += float(s.tien_ck or 0)

    # =========================
    # NHẬP HÀNG
    # =========================

    purchase_query = db.query(HoaDonNhap).filter(
        HoaDonNhap.ngay == ngay,
        HoaDonNhap.trang_thai == "xac_nhan"
    )

    purchase_query = filter_nv(purchase_query, HoaDonNhap)

    purchases = purchase_query.all()

    tong_nhap = sum(float(p.tong_tien or 0) for p in purchases)

    # =========================
    # THU CHI (FIX TIME RANGE)
    # =========================

    thu_chi_query = db.query(ThuChi).filter(
        ThuChi.ngay >= start,
        ThuChi.ngay <= end
    )

    thu_chi_query = filter_nv(thu_chi_query, ThuChi)

    thu_chi = thu_chi_query.all()

    tong_thu = 0
    tong_chi = 0

    for t in thu_chi:
        so_tien = float(t.so_tien or 0)

        if t.loai == "thu":
            tong_thu += so_tien
        else:
            tong_chi += so_tien

    # =========================
    # ADMIN: BREAKDOWN
    # =========================

    breakdown = []

    if is_admin:
        data_nv = (
            db.query(
                ThuChi.ma_nv,
                func.sum(
                    func.case(
                        (ThuChi.loai == "thu", ThuChi.so_tien),
                        else_=0
                    )
                ).label("tong_thu"),
                func.sum(
                    func.case(
                        (ThuChi.loai == "chi", ThuChi.so_tien),
                        else_=0
                    )
                ).label("tong_chi"),
            )
            .filter(ThuChi.ngay >= start, ThuChi.ngay <= end)
            .group_by(ThuChi.ma_nv)
            .all()
        )

        for row in data_nv:
            breakdown.append({
                "ma_nv": row.ma_nv,
                "tong_thu": float(row.tong_thu or 0),
                "tong_chi": float(row.tong_chi or 0)
            })

    # =========================
    # KẾT QUẢ
    # =========================

    return {
        "tong_ket": {
            "tong_so_binh_ban": tong_so_binh_ban,
            "tong_ban": tong_ban,
            "tong_nhap": tong_nhap,
            "tong_tien_mat": tong_tien_mat,
            "tong_chuyen_khoan": tong_tien_ck,
            "tong_thu": tong_thu,
            "tong_chi": tong_chi,
            "ton_quy": tong_tien_mat + tong_tien_ck + tong_thu - tong_chi - tong_nhap
        },
        "breakdown_nhan_vien": breakdown if is_admin else None
    }
