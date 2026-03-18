from app.database import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime


# ==============================
# NHÂN VIÊN
# ==============================

class NhanVien(Base):
    __tablename__ = "nhan_vien"

    id = Column(Integer, primary_key=True)
    ma_nv = Column(String(50), unique=True, nullable=False)
    ten_nv = Column(String(255))
    vai_tro = Column(Enum("admin", "ke_toan", "nv_dac_biet", "nhan_vien", "ke_toan_online"))
    trang_thai = Column(Enum("hoat_dong", "ngung"), default="hoat_dong")
    password_hash = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# KHO HÀNG
# ==============================

class KhoHang(Base):
    __tablename__ = "kho_hang"

    id = Column(Integer, primary_key=True)
    ma_kho = Column(String(20), unique=True, nullable=False)
    ten_kho = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# NHÀ CUNG CẤP
# ==============================

class NhaCungCap(Base):
    __tablename__ = "nha_cung_cap"

    id = Column(Integer, primary_key=True)
    ma_ncc = Column(String(50), unique=True, nullable=False)
    ten_ncc = Column(String(255))
    dia_chi = Column(String(255))
    so_dien_thoai = Column(String(20))
    ma_so_thue = Column(String(50))
    email = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# KHÁCH HÀNG
# ==============================

class KhachHang(Base):
    __tablename__ = "khach_hang"

    id = Column(Integer, primary_key=True)
    ma_kh = Column(String(50), unique=True, nullable=False)
    ten_cua_hang = Column(String(255))
    ten_cua_hang_chi_tiet = Column(String(255))
    dia_chi = Column(String(255))
    so_dien_thoai = Column(String(20))
    ma_so_thue = Column(String(50))
    ghi_chu = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# SẢN PHẨM
# ==============================

class SanPham(Base):
    __tablename__ = "san_pham"

    id = Column(Integer, primary_key=True)
    ma_sp = Column(String(50), unique=True, nullable=False)
    ten_sp = Column(String(255))
    loai_san_pham = Column(Enum("gas_binh", "gas_kg", "gas_mini", "khac"))
    don_vi_tinh = Column(Enum("binh", "kg", "lon", "cai"))
    dung_tich_kg = Column(DECIMAL(6, 2))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# HÓA ĐƠN NHẬP
# ==============================

class HoaDonNhap(Base):
    __tablename__ = "hoa_don_nhap"

    id = Column(Integer, primary_key=True)
    ngay = Column(Date)
    ma_ncc = Column(String(50), ForeignKey("nha_cung_cap.ma_ncc"))
    ma_nv = Column(String(50), ForeignKey("nhan_vien.ma_nv"))
    ma_kho = Column(String(20), ForeignKey("kho_hang.ma_kho"))

    tong_tien = Column(DECIMAL(18, 2))
    tien_mat = Column(DECIMAL(18, 2))
    tien_ck = Column(DECIMAL(18, 2))
    tong_thanh_toan = Column(DECIMAL(18, 2))

    trang_thai = Column(Enum("nhap", "xac_nhan", "chot", "huy"), default="nhap")

    ngay_tao = Column(DateTime, default=datetime.utcnow)

    items = relationship("HoaDonNhapChiTiet", back_populates="hoa_don")


class HoaDonNhapChiTiet(Base):
    __tablename__ = "hoa_don_nhap_chi_tiet"

    id = Column(Integer, primary_key=True)
    id_hoa_don = Column(Integer, ForeignKey("hoa_don_nhap.id"))
    ma_sp = Column(String(50), ForeignKey("san_pham.ma_sp"))

    so_luong = Column(DECIMAL(10, 2))
    don_gia = Column(DECIMAL(18, 2))
    thanh_tien = Column(DECIMAL(18, 2))

    hoa_don = relationship("HoaDonNhap", back_populates="items")


# ==============================
# HÓA ĐƠN BÁN
# ==============================

class HoaDonBan(Base):
    __tablename__ = "hoa_don_ban"

    id = Column(Integer, primary_key=True)
    so_hd = Column(String(50))

    ngay = Column(Date)

    ma_kh = Column(String(50), ForeignKey("khach_hang.ma_kh"))
    ma_nv = Column(String(50), ForeignKey("nhan_vien.ma_nv"))
    ma_kho = Column(String(20), ForeignKey("kho_hang.ma_kho"))

    tong_tien = Column(DECIMAL(18, 2))
    tien_mat = Column(DECIMAL(18, 2))
    tien_ck = Column(DECIMAL(18, 2))
    tong_thanh_toan = Column(DECIMAL(18, 2))

    no_lai = Column(DECIMAL(18, 2))

    trang_thai = Column(Enum("nhap", "xac_nhan", "chot", "huy"), default="nhap")

    ngay_tao = Column(DateTime, default=datetime.utcnow)


class HoaDonBanChiTiet(Base):
    __tablename__ = "hoa_don_ban_chi_tiet"

    id = Column(Integer, primary_key=True)
    id_hoa_don = Column(Integer, ForeignKey("hoa_don_ban.id"))
    ma_sp = Column(String(50), ForeignKey("san_pham.ma_sp"))

    so_luong = Column(DECIMAL(10, 2))
    don_gia = Column(DECIMAL(18, 2))
    thanh_tien = Column(DECIMAL(18, 2))


# ==============================
# NHẬT KÝ KHO
# ==============================

class NhatKyKho(Base):
    __tablename__ = "nhat_ky_kho"

    id = Column(Integer, primary_key=True)

    ngay = Column(DateTime)

    ma_sp = Column(String(50))
    ma_kho = Column(String(20))

    so_luong = Column(DECIMAL(10, 2))

    loai = Column(Enum("nhap", "xuat"))

    bang_tham_chieu = Column(String(50))
    id_tham_chieu = Column(Integer)

    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# THU CHI
# ==============================

class ThuChi(Base):
    __tablename__ = "thu_chi"

    id = Column(Integer, primary_key=True)

    ngay = Column(DateTime, nullable=False)

    doi_tuong = Column(Enum("nhan_vien", "cong_ty"))

    ma_nv = Column(String(50), ForeignKey("nhan_vien.ma_nv"))

    so_tien = Column(DECIMAL(18, 2))

    loai = Column(Enum("thu", "chi"))

    hinh_thuc = Column(Enum("tien_mat", "chuyen_khoan"))

    loai_giao_dich = Column(String(100))

    noi_dung = Column(String(255))

    so_du_sau = Column(DECIMAL(18, 2))

    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# QUỸ NHÂN VIÊN CHỐT NGÀY
# ==============================

class QuyNhanVienChotNgay(Base):
    __tablename__ = "quy_nhan_vien_chot_ngay"

    id = Column(Integer, primary_key=True)

    ngay_chot = Column(Date)

    ma_nv = Column(String(50))

    so_du = Column(DECIMAL(18, 2))

    so_du_luy_ke = Column(DECIMAL(18, 2))

    ngay_tao = Column(DateTime)


# ==============================
# QUỸ CÔNG TY CHỐT NGÀY
# ==============================

# ==============================
# QUỸ CÔNG TY CHỐT NGÀY
# ==============================

class QuyCongTyChotNgay(Base):
    __tablename__ = "quy_cong_ty_chot_ngay"

    id = Column(Integer, primary_key=True)

    ngay_chot = Column(Date)

    tien_mat = Column(DECIMAL(18,2))

    tien_ngan_hang = Column(DECIMAL(18,2))

    tong_quy = Column(DECIMAL(18,2))

    ngay_tao = Column(DateTime)

# ==============================
# TỒN KHO CHỐT NGÀY
# ==============================

class TonKhoChotNgay(Base):
    __tablename__ = "ton_kho_chot_ngay"

    id = Column(Integer, primary_key=True)

    ngay_chot = Column(Date)

    ma_sp = Column(String(50))

    ma_kho = Column(String(20))

    so_luong = Column(DECIMAL(10, 2))

    ngay_tao = Column(DateTime)
