from app.database import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime


# ==============================
# NHÂN VIÊN
# ==============================
class NhanVien(Base):
    __tablename__ = "nhan_vien"

    id = Column(Integer, primary_key=True, index=True)
    ma_nv = Column(String(50), unique=True, index=True, nullable=False)
    ten_nv = Column(String(255))
    vai_tro = Column(Enum("admin", "ke_toan", "nv_dac_biet", "nhan_vien", "ke_toan_online"), nullable=False)
    trang_thai = Column(Enum("hoat_dong", "ngung"), default="hoat_dong")
    password_hash = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# KHO HÀNG
# ==============================
class KhoHang(Base):
    __tablename__ = "kho_hang"

    id = Column(Integer, primary_key=True, index=True)
    ma_kho = Column(String(20), unique=True, nullable=False)
    ten_kho = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# SẢN PHẨM
# ==============================
class SanPham(Base):
    __tablename__ = "san_pham"

    id = Column(Integer, primary_key=True, index=True)
    ma_sp = Column(String(50), unique=True, nullable=False)
    ten_sp = Column(String(255))
    loai_san_pham = Column(Enum("gas_binh", "gas_kg", "gas_mini", "khac"))
    don_vi_tinh = Column(Enum("binh", "kg", "lon", "cai"))
    dung_tich_kg = Column(DECIMAL(6, 2))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# NHÀ CUNG CẤP
# ==============================
class NhaCungCap(Base):
    __tablename__ = "nha_cung_cap"

    id = Column(Integer, primary_key=True, index=True)
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

    id = Column(Integer, primary_key=True, index=True)
    ma_kh = Column(String(50), unique=True, nullable=False)
    ten_cua_hang = Column(String(255))
    ten_cua_hang_chi_tiet = Column(String(255))
    dia_chi = Column(String(255))
    so_dien_thoai = Column(String(20))
    ma_so_thue = Column(String(50))
    ghi_chu = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# HÓA ĐƠN NHẬP
# ==============================
class HoaDonNhap(Base):
    __tablename__ = "hoa_don_nhap"

    id = Column(Integer, primary_key=True, index=True)
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

    id = Column(Integer, primary_key=True, index=True)
    id_hoa_don = Column(Integer, ForeignKey("hoa_don_nhap.id"))
    ma_sp = Column(String(50), ForeignKey("san_pham.ma_sp"))

    so_luong = Column(DECIMAL(10, 2))
    don_gia = Column(DECIMAL(18, 2))
    thanh_tien = Column(DECIMAL(18, 2))

    hoa_don = relationship("HoaDonNhap", back_populates="items")


# ==============================
# NHẬT KÝ KHO
# ==============================
class NhatKyKho(Base):
    __tablename__ = "nhat_ky_kho"

    id = Column(Integer, primary_key=True, index=True)
    ngay = Column(DateTime)
    ma_sp = Column(String(50))
    ma_kho = Column(String(20))
    so_luong = Column(DECIMAL(10, 2))
    loai = Column(Enum("nhap", "xuat"))
    bang_tham_chieu = Column(String(50))
    id_tham_chieu = Column(Integer)
    ngay_tao = Column(DateTime, default=datetime.utcnow)
