# (giữ nguyên import cũ)
from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import HTTPException
from datetime import date

from app.models import (
    HoaDonNhap,
    HoaDonNhapChiTiet,
    HoaDonBan,
    HoaDonBanChiTiet,
    NhatKyKho,
    ThuChi,
    NhanVien,
    KhachHang,
    GasDu,
    SanPham
)

from app.schemas import HoaDonNhapCreate, HoaDonBanCreate


# =====================================================
# TIME VN
# =====================================================

def now_vn():
    return datetime.utcnow() + timedelta(hours=7)


# =====================================================
# CORE GAS DƯ (LEDGER)
# =====================================================

def apply_gas_du(
    db: Session,
    *,
    ma_sp_goc: str,
    ma_kho: str,
    delta_kg: float,
    loai: str,
    ref_id: int = None,
    ref_type: str = None,
    ma_kh: str = None,
    ma_nv: str = None,
    ghi_chu: str = None,
):
    delta_kg = Decimal(str(delta_kg))

    last_row = (
        db.query(GasDu)
        .filter(
            GasDu.ma_sp_goc == ma_sp_goc,
            GasDu.ma_kho == ma_kho,
        )
        .order_by(desc(GasDu.id))
        .with_for_update()
        .first()
    )

    ton_truoc = last_row.ton_sau_kg if last_row else Decimal("0")
    ton_moi = ton_truoc + delta_kg

    if ton_moi < 0:
        raise HTTPException(400, f"Không đủ gas dư: {ma_sp_goc}")

    new_row = GasDu(
        thoi_diem=now_vn(),
        loai=loai,
        ma_sp_goc=ma_sp_goc,
        ma_kho=ma_kho,
        so_kg=delta_kg,
        ton_sau_kg=ton_moi,
        id_hoa_don_ban=ref_id if ref_type == "sale" else None,
        id_phieu_nhap=ref_id if ref_type == "import" else None,
        ma_kh=ma_kh,
        ma_nv=ma_nv,
        ghi_chu=ghi_chu,
        ref_type=ref_type,
        created_at=now_vn(),
    )

    db.add(new_row)


# =====================================================
# NHẬP HÀNG (FIX TIME)
# =====================================================

def create_hoa_don_nhap(db: Session, data: HoaDonNhapCreate, user: NhanVien):

    if not data.items:
        raise HTTPException(400, "Không có sản phẩm")

    with db.begin():

        tong_tien = Decimal("0")

        for item in data.items:
            tong_tien += Decimal(str(item.so_luong)) * Decimal(str(item.don_gia))

        hoa_don = HoaDonNhap(
            ngay=now_vn(),
            ma_ncc=data.ma_ncc,
            ma_nv=user.ma_nv,
            ma_kho=data.ma_kho,
            trang_thai="nhap",
            tien_mat=data.tien_mat,
            tien_ck=data.tien_ck
        )

        db.add(hoa_don)
        db.flush()

        for item in data.items:

            thanh_tien = Decimal(str(item.so_luong)) * Decimal(str(item.don_gia))

            db.add(HoaDonNhapChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            ))

            db.add(NhatKyKho(
                ngay=now_vn(),
                ma_sp=item.ma_sp,
                ma_kho=data.ma_kho,
                so_luong=item.so_luong,
                loai="nhap",
                bang_tham_chieu="hoa_don_nhap",
                id_tham_chieu=hoa_don.id,
                ma_nv=user.ma_nv
            ))

        hoa_don.tong_tien = tong_tien
        hoa_don.tong_thanh_toan = tong_tien

        return hoa_don


# =====================================================
# BÁN HÀNG (GẮN GAS DƯ)
# =====================================================

def create_hoa_don_ban(db: Session, data: HoaDonBanCreate, user: NhanVien):

    with db.begin():

        tong_tien = Decimal("0")

        hoa_don = HoaDonBan(
            ngay=data.ngay,
            ma_kh=data.ma_kh,
            ma_nv=user.ma_nv,
            ma_kho=data.ma_kho,
            tien_mat=data.tien_mat,
            tien_ck=data.tien_ck,
            trang_thai="xac_nhan"
        )

        db.add(hoa_don)
        db.flush()

        for item in data.items:

            sp = db.query(SanPham).filter(
                SanPham.ma_sp == item.ma_sp
            ).first()

            if not sp:
                raise HTTPException(400, f"Không có SP {item.ma_sp}")

            dinh_muc = Decimal(str(sp.dung_tich_kg or 0))
            so_ban = Decimal(str(item.so_luong))

            # ===== GAS DƯ LOGIC =====
            if dinh_muc > 0:

                if so_ban < dinh_muc:
                    du = dinh_muc - so_ban

                    apply_gas_du(
                        db,
                        ma_sp_goc=item.ma_sp,
                        ma_kho=data.ma_kho,
                        delta_kg=float(du),
                        loai="phat_sinh",
                        ref_id=hoa_don.id,
                        ref_type="sale",
                        ma_kh=data.ma_kh,
                        ma_nv=user.ma_nv,
                    )

                elif so_ban > dinh_muc:
                    thieu = so_ban - dinh_muc

                    apply_gas_du(
                        db,
                        ma_sp_goc=item.ma_sp,
                        ma_kho=data.ma_kho,
                        delta_kg=float(-thieu),
                        loai="ban",
                        ref_id=hoa_don.id,
                        ref_type="sale",
                        ma_kh=data.ma_kh,
                        ma_nv=user.ma_nv,
                    )

            thanh_tien = so_ban * Decimal(str(item.don_gia))
            tong_tien += thanh_tien

            db.add(HoaDonBanChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            ))

        hoa_don.tong_tien = tong_tien
        hoa_don.tong_thanh_toan = data.tien_mat + data.tien_ck
        hoa_don.no_lai = tong_tien - (data.tien_mat + data.tien_ck)

        return hoa_don
