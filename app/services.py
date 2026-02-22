# app/services.py

from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

from app.models import HoaDonNhap, HoaDonNhapChiTiet, NhatKyKho
from app.schemas import HoaDonNhapCreate


def create_hoa_don_nhap(db: Session, data: HoaDonNhapCreate, ma_nv: str):

    with db.begin():

        tong_tien = Decimal(0)

        hoa_don = HoaDonNhap(
            ngay=data.ngay,
            ma_ncc=data.ma_ncc,
            ma_nv=ma_nv,
            ma_kho=data.ma_kho,
            trang_thai="nhap",
            tien_mat=data.tien_mat,
            tien_ck=data.tien_ck
        )

        db.add(hoa_don)
        db.flush()   # Lấy ID

        for item in data.items:

            thanh_tien = Decimal(item.so_luong) * Decimal(item.don_gia)
            tong_tien += thanh_tien

            # 1️⃣ Thêm chi tiết hóa đơn
            chi_tiet = HoaDonNhapChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            )
            db.add(chi_tiet)

            # 2️⃣ Ghi nhật ký kho
            nhat_ky = NhatKyKho(
                ngay=datetime.utcnow(),
                ma_sp=item.ma_sp,
                ma_kho=data.ma_kho,
                so_luong=item.so_luong,
                loai="nhap",
                bang_tham_chieu="hoa_don_nhap",
                id_tham_chieu=hoa_don.id
            )
            db.add(nhat_ky)

        hoa_don.tong_tien = tong_tien
        hoa_don.tong_thanh_toan = tong_tien
