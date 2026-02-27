# app/services.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime

from app.models import (
    HoaDonNhap,
    HoaDonNhapChiTiet,
    HoaDonBan,
    HoaDonBanChiTiet,
    NhatKyKho,
    ThuChi,
    NhanVien
)

from app.schemas import HoaDonNhapCreate, HoaDonBanCreate


# =====================================================
# NHẬP HÀNG
# =====================================================
def create_hoa_don_nhap(db: Session, data: HoaDonNhapCreate, user: NhanVien):

    try:
        tong_tien = Decimal("0")

        hoa_don = HoaDonNhap(
            ngay=data.ngay,
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
            tong_tien += thanh_tien

            db.add(HoaDonNhapChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            ))

            db.add(NhatKyKho(
                ngay=datetime.utcnow(),
                ma_sp=item.ma_sp,
                ma_kho=data.ma_kho,
                so_luong=item.so_luong,
                loai="nhap",
                bang_tham_chieu="hoa_don_nhap",
                id_tham_chieu=hoa_don.id
            ))

        hoa_don.tong_tien = tong_tien
        hoa_don.tong_thanh_toan = tong_tien

        # ===== XỬ LÝ TIỀN CHI =====
        tien_mat = Decimal(str(data.tien_mat))
        tien_ck = Decimal(str(data.tien_ck))

        if tien_mat > 0:
            db.add(ThuChi(
                ngay=datetime.utcnow(),
                doi_tuong="cong_ty",
                ma_nv=user.ma_nv,
                so_tien=tien_mat,
                loai="chi",
                hinh_thuc="tien_mat",
                noi_dung=f"Chi tiền mặt nhập hàng HĐ {hoa_don.id}"
            ))

        if tien_ck > 0:
            db.add(ThuChi(
                ngay=datetime.utcnow(),
                doi_tuong="cong_ty",
                ma_nv=user.ma_nv,
                so_tien=tien_ck,
                loai="chi",
                hinh_thuc="chuyen_khoan",
                noi_dung=f"Chi chuyển khoản nhập hàng HĐ {hoa_don.id}"
            ))

        db.commit()
        db.refresh(hoa_don)
        return hoa_don

    except Exception as e:
        db.rollback()
        raise e


# =====================================================
# BÁN HÀNG (LOGIC TIỀN CHUẨN)
# =====================================================
def create_hoa_don_ban(db: Session, data: HoaDonBanCreate, user: NhanVien):

    try:
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

        # ===== XỬ LÝ TỒN =====
        for item in data.items:

            tong_nhap = db.query(func.coalesce(func.sum(NhatKyKho.so_luong), 0)).filter(
                NhatKyKho.ma_sp == item.ma_sp,
                NhatKyKho.ma_kho == data.ma_kho,
                NhatKyKho.loai == "nhap"
            ).scalar()

            tong_xuat = db.query(func.coalesce(func.sum(NhatKyKho.so_luong), 0)).filter(
                NhatKyKho.ma_sp == item.ma_sp,
                NhatKyKho.ma_kho == data.ma_kho,
                NhatKyKho.loai == "xuat"
            ).scalar()

            so_ton = Decimal(str(tong_nhap)) - Decimal(str(tong_xuat))

            if so_ton < Decimal(str(item.so_luong)):
                raise Exception(f"Tồn kho không đủ cho {item.ma_sp}")

            thanh_tien = Decimal(str(item.so_luong)) * Decimal(str(item.don_gia))
            tong_tien += thanh_tien

            db.add(HoaDonBanChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            ))

            db.add(NhatKyKho(
                ngay=datetime.utcnow(),
                ma_sp=item.ma_sp,
                ma_kho=data.ma_kho,
                so_luong=item.so_luong,
                loai="xuat",
                bang_tham_chieu="hoa_don_ban",
                id_tham_chieu=hoa_don.id
            ))

        hoa_don.tong_tien = tong_tien
        hoa_don.tong_thanh_toan = tong_tien

        # ===== XỬ LÝ TIỀN =====
        tien_mat = Decimal(str(data.tien_mat))
        tien_ck = Decimal(str(data.tien_ck))

        # Tiền mặt
        if tien_mat > 0:

            if user.vai_tro == "nv_dac_biet":

                db.add(ThuChi(
                    ngay=datetime.utcnow(),
                    doi_tuong="nhan_vien",
                    ma_nv=user.ma_nv,
                    so_tien=tien_mat,
                    loai="thu",
                    hinh_thuc="tien_mat",
                    noi_dung=f"Thu tiền mặt HĐ {hoa_don.id}"
                ))

            else:

                db.add(ThuChi(
                    ngay=datetime.utcnow(),
                    doi_tuong="cong_ty",
                    ma_nv=user.ma_nv,
                    so_tien=tien_mat,
                    loai="thu",
                    hinh_thuc="tien_mat",
                    noi_dung=f"Thu tiền mặt HĐ {hoa_don.id}"
                ))

        # Chuyển khoản luôn vào ngân hàng công ty
        if tien_ck > 0:

            db.add(ThuChi(
                ngay=datetime.utcnow(),
                doi_tuong="cong_ty",
                ma_nv=user.ma_nv,
                so_tien=tien_ck,
                loai="thu",
                hinh_thuc="chuyen_khoan",
                noi_dung=f"Thu chuyển khoản HĐ {hoa_don.id}"
            ))

        db.commit()
        db.refresh(hoa_don)
        return hoa_don

    except Exception as e:
        db.rollback()
        raise e
