# app/services.py

from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

from app.models import HoaDonNhap, HoaDonNhapChiTiet, NhatKyKho
from app.schemas import HoaDonNhapCreate


def create_hoa_don_nhap(db: Session, data: HoaDonNhapCreate, ma_nv: str):

    try:
        tong_tien = Decimal("0")

        # 1️⃣ Tạo hóa đơn nhập
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
        db.flush()  # Lấy ID ngay

        # 2️⃣ Thêm chi tiết + nhật ký kho
        for item in data.items:
            thanh_tien = Decimal(str(item.so_luong)) * Decimal(str(item.don_gia))
            tong_tien += thanh_tien

            chi_tiet = HoaDonNhapChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            )
            db.add(chi_tiet)

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

        # 3️⃣ Cập nhật tổng tiền
        hoa_don.tong_tien = tong_tien
        hoa_don.tong_thanh_toan = tong_tien

        # 4️⃣ Commit
        db.commit()
        db.refresh(hoa_don)

        return hoa_don

    except Exception as e:
        db.rollback()
        raise e
