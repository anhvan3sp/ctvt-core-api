# app/services.py

from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from app.models import HoaDonNhap, HoaDonNhapChiTiet, NhatKyKho, ThuChi
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

def create_hoa_don_ban(db: Session, data: HoaDonBanCreate, ma_nv: str):

    try:
        tong_tien = Decimal("0")

        hoa_don = HoaDonBan(
            ngay=data.ngay,
            ma_kh=data.ma_kh,
            ma_nv=ma_nv,
            ma_kho=data.ma_kho,
            tien_mat=data.tien_mat,
            tien_ck=data.tien_ck,
            trang_thai="xac_nhan"
        )

        db.add(hoa_don)
        db.flush()

        for item in data.items:

            # 🔎 TÍNH TỒN REALTIME
            nhat_ky = db.query(NhatKyKho).filter(
                NhatKyKho.ma_sp == item.ma_sp,
                NhatKyKho.ma_kho == data.ma_kho
            ).all()

            tong_nhap = sum([float(n.so_luong) for n in nhat_ky if n.loai == "nhap"])
            tong_xuat = sum([float(n.so_luong) for n in nhat_ky if n.loai == "xuat"])

            so_ton = tong_nhap - tong_xuat

            if so_ton < item.so_luong:
                raise Exception(f"Tồn kho không đủ cho {item.ma_sp}")

            thanh_tien = Decimal(str(item.so_luong)) * Decimal(str(item.don_gia))
            tong_tien += thanh_tien

            # Thêm chi tiết
            db.add(HoaDonBanChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            ))

            # Trừ kho
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

        # Tính nợ
        da_thu = Decimal(str(data.tien_mat)) + Decimal(str(data.tien_ck))
        hoa_don.no_lai = tong_tien - da_thu

        # Nếu có tiền thu → ghi thu_chi
        if da_thu > 0:
            db.add(ThuChi(
                ngay=datetime.utcnow(),
                doi_tuong="cong_ty",
                ma_nv=ma_nv,
                so_tien=da_thu,
                loai="thu",
                hinh_thuc="tien_mat" if data.tien_mat > 0 else "chuyen_khoan",
                noi_dung=f"Thu tiền bán hàng HĐ {hoa_don.id}"
            ))

        db.commit()
        db.refresh(hoa_don)
        return hoa_don

    except Exception as e:
        db.rollback()
        raise e
