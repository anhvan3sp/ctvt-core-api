from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, DECIMAL
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
# KHO
# ==============================

class KhoHang(Base):
    __tablename__ = "kho_hang"

    id = Column(Integer, primary_key=True)
    ma_kho = Column(String(20), unique=True, nullable=False)
    ten_kho = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# NCC
# ==============================

class NhaCungCap(Base):
    __tablename__ = "nha_cung_cap"

    id = Column(Integer, primary_key=True)
    ma_ncc = Column(String(50), unique=True, nullable=False)
    ten_ncc = Column(String(255))
    cong_no = Column(DECIMAL(18,2), default=0)  # 🔥 thêm
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# KHÁCH
# ==============================

class KhachHang(Base):
    __tablename__ = "khach_hang"

    id = Column(Integer, primary_key=True)
    ma_kh = Column(String(50), unique=True, nullable=False)
    ten_cua_hang = Column(String(255))
    cong_no = Column(DECIMAL(18,2), default=0)  # 🔥 thêm
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# SẢN PHẨM
# ==============================

class SanPham(Base):
    __tablename__ = "san_pham"

    id = Column(Integer, primary_key=True)
    ma_sp = Column(String(50), unique=True, nullable=False)
    ten_sp = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# NHẬT KÝ KHO
# ==============================

class NhatKyKho(Base):
    __tablename__ = "nhat_ky_kho"

    id = Column(Integer, primary_key=True)
    ngay = Column(DateTime, default=datetime.utcnow)

    ma_sp = Column(String(50))
    ma_kho = Column(String(20))
    ma_nv = Column(String(20))

    so_luong = Column(DECIMAL(10, 2))
    loai = Column(Enum("nhap", "xuat"))

    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# THU CHI
# ==============================

class ThuChi(Base):
    __tablename__ = "thu_chi"

    id = Column(Integer, primary_key=True)

    ngay = Column(DateTime, default=datetime.utcnow)

    ma_nv = Column(String(50))
    so_tien = Column(DECIMAL(18, 2))

    loai = Column(Enum("thu", "chi"))
    hinh_thuc = Column(Enum("tien_mat", "chuyen_khoan"))

    loai_giao_dich = Column(String(100))

    so_du_sau = Column(DECIMAL(18, 2))
    so_du_ct_sau = Column(DECIMAL(18, 2))  # 🔥 thêm

    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# QUỸ NHÂN VIÊN (1 dòng / NV)
# ==============================

class QuyNhanVienChotNgay(Base):
    __tablename__ = "quy_nhan_vien_chot_ngay"

    id = Column(Integer, primary_key=True)
    ma_nv = Column(String(50), unique=True)

    so_du = Column(DECIMAL(18, 2), default=0)

    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# QUỸ CÔNG TY (1 dòng)
# ==============================

class QuyCongTyChotNgay(Base):
    __tablename__ = "quy_cong_ty_chot_ngay"

    id = Column(Integer, primary_key=True)

    tien_mat = Column(DECIMAL(18,2), default=0)
    tien_ngan_hang = Column(DECIMAL(18,2), default=0)
    tong_quy = Column(DECIMAL(18,2), default=0)

    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ==============================
# TỒN KHO (1 dòng / kho + sp)
# ==============================

class TonKhoChotNgay(Base):
    __tablename__ = "ton_kho_chot_ngay"

    id = Column(Integer, primary_key=True)

    ma_sp = Column(String(50))
    ma_kho = Column(String(20))

    so_luong = Column(DECIMAL(10, 2), default=0)

    ngay_tao = Column(DateTime, default=datetime.utcnow)
