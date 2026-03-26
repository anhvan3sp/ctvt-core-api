from app.database import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey, DECIMAL, func, BigInteger, Text, CheckConstraint, Index, text
from datetime import datetime
import enum

# =========================
# ENUM KHỚP THU_CHI
# =========================

class LoaiPhatSinh(str, enum.Enum):
    THU = "thu"
    CHI = "chi"


class TrangThaiPhatSinh(str, enum.Enum):
    NHAP = "nhap"
    XAC_NHAN = "xac_nhan"
    HUY = "huy"


# =========================
# MODEL PHÁT SINH
# =========================

class PhatSinh(Base):
    __tablename__ = "phat_sinh"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    ma_nv = Column(
        String(20),
        ForeignKey("nhan_vien.ma_nv", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    ngay = Column(Date, nullable=False, index=True)

    thoi_diem = Column(
        DateTime,
        nullable=True,
        server_default=func.now()
    )

    # 🔥 FIX 1: ENUM → STRING
    loai = Column(
        String(10),
        nullable=False,
        index=True
    )

    loai_giao_dich = Column(String(50), nullable=True)

    so_tien = Column(DECIMAL(18, 2), nullable=False)

    dien_giai = Column(Text, nullable=True)

    ref_id = Column(BigInteger, nullable=True)
    ref_type = Column(String(50), nullable=True)

    # =========================
    # CORE ERP
    # =========================

    # 🔥 FIX 2: ENUM → STRING
    trang_thai = Column(
        String(20),
        nullable=False,
        server_default=text("'nhap'"),
        index=True
    )

    id_thu_chi = Column(BigInteger, nullable=True, index=True)

    id_thu_chi_dao = Column(BigInteger, nullable=True, index=True)

    idempotency_key = Column(String(100), nullable=True)

    created_at = Column(
        DateTime,
        nullable=True,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        nullable=True,
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("so_tien >= 0", name="phat_sinh_chk_1"),

        Index("idx_ma_nv", "ma_nv"),
        Index("idx_ngay", "ngay"),
        Index("idx_loai", "loai"),
        Index("idx_trang_thai", "trang_thai"),
        Index("idx_ps_idem", "idempotency_key"),
    )


# ======================
# NHÂN VIÊN
# ======================
class NhanVien(Base):
    __tablename__ = "nhan_vien"

    id = Column(Integer, primary_key=True)
    ma_nv = Column(String(50), unique=True, nullable=False)
    ten_nv = Column(String(255))
    vai_tro = Column(Enum("admin","ke_toan","nv_dac_biet","nhan_vien","ke_toan_online"))
    trang_thai = Column(Enum("hoat_dong","ngung"), default="hoat_dong")
    password_hash = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ======================
# KHO
# ======================
class KhoHang(Base):
    __tablename__ = "kho_hang"

    id = Column(Integer, primary_key=True)
    ma_kho = Column(String(20), unique=True, nullable=False)
    ten_kho = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ======================
# NHÂN VIÊN - KHO
# ======================
class NhanVienKho(Base):
    __tablename__ = "nhan_vien_kho"

    id = Column(Integer, primary_key=True)
    ma_nv = Column(String(50), ForeignKey("nhan_vien.ma_nv"))
    ma_kho = Column(String(20), ForeignKey("kho_hang.ma_kho"))


# ======================
# KHÁCH HÀNG
# ======================
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


# ======================
# NHÀ CUNG CẤP
# ======================
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


# ======================
# SẢN PHẨM
# ======================
class SanPham(Base):
    __tablename__ = "san_pham"

    id = Column(Integer, primary_key=True)
    ma_sp = Column(String(50), unique=True, nullable=False)
    ten_sp = Column(String(255))
    loai_san_pham = Column(Enum("gas_binh","gas_kg","gas_mini","khac"))
    don_vi_tinh = Column(Enum("binh","kg","lon","cai"))
    dung_tich_kg = Column(DECIMAL(6,2))
    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ======================
# HÓA ĐƠN NHẬP (GIỮ NGUYÊN)
# ======================
class HoaDonNhap(Base):
    __tablename__ = "hoa_don_nhap"

    id = Column(Integer, primary_key=True)
    ngay = Column(Date)

    ma_ncc = Column(String(50), ForeignKey("nha_cung_cap.ma_ncc"))
    ma_nv = Column(String(50), ForeignKey("nhan_vien.ma_nv"))
    ma_kho = Column(String(20), ForeignKey("kho_hang.ma_kho"))

    tong_tien = Column(DECIMAL(18,2))
    tien_mat = Column(DECIMAL(18,2))
    tien_ck = Column(DECIMAL(18,2))
    tong_thanh_toan = Column(DECIMAL(18,2))

    trang_thai = Column(Enum("nhap","xac_nhan","chot","huy"))
    ngay_tao = Column(DateTime, default=datetime.utcnow)
