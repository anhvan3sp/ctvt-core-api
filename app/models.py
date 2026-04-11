import enum
from datetime import datetime
from sqlalchemy.sql import func


from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Enum, ForeignKey,
    DECIMAL, BigInteger, Text, CheckConstraint, Index, Numeric
)
from app.database import Base


# =========================
# ENUM
# =========================

class LoaiPhatSinh(str, enum.Enum):
    THU = "thu"
    CHI = "chi"


class TrangThaiPhatSinh(str, enum.Enum):
    NHAP = "nhap"
    XAC_NHAN = "xac_nhan"
    HUY = "huy"


# =========================
# PHÁT SINH
# =========================

class PhatSinh(Base):
    __tablename__ = "phat_sinh"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    ma_nv = Column(String(20), ForeignKey("nhan_vien.ma_nv"), nullable=False, index=True)

    ngay = Column(Date, nullable=False, index=True)

    thoi_diem = Column(DateTime, default=datetime.now)

    loai = Column(String(10), nullable=False, index=True)

    loai_giao_dich = Column(String(50), nullable=True)

    so_tien = Column(DECIMAL(18, 2), nullable=False)

    dien_giai = Column(Text, nullable=True)

    ref_id = Column(BigInteger, nullable=True)
    ref_type = Column(String(50), nullable=True)

    trang_thai = Column(String(20), nullable=False, default="nhap", index=True)

    id_thu_chi = Column(BigInteger, nullable=True, index=True)
    id_thu_chi_dao = Column(BigInteger, nullable=True, index=True)

    idempotency_key = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

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
    ngay_tao = Column(DateTime, default=datetime.now)


# ======================
# KHO
# ======================
class KhoHang(Base):
    __tablename__ = "kho_hang"

    id = Column(Integer, primary_key=True)
    ma_kho = Column(String(20), unique=True, nullable=False)
    ten_kho = Column(String(255))
    ngay_tao = Column(DateTime, default=datetime.now)


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
    ngay_tao = Column(DateTime, default=datetime.now)


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
    ngay_tao = Column(DateTime, default=datetime.now)


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
    ngay_tao = Column(DateTime, default=datetime.now)


# ======================
# HÓA ĐƠN NHẬP
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
    ngay_tao = Column(DateTime, default=datetime.now)


class HoaDonNhapChiTiet(Base):
    __tablename__ = "hoa_don_nhap_chi_tiet"

    id = Column(Integer, primary_key=True)
    id_hoa_don = Column(Integer, ForeignKey("hoa_don_nhap.id"))
    ma_sp = Column(String(50), ForeignKey("san_pham.ma_sp"))

    so_luong = Column(DECIMAL(10,2))
    don_gia = Column(DECIMAL(18,2))
    thanh_tien = Column(DECIMAL(18,2))


# ======================
# HÓA ĐƠN BÁN
# ======================
class HoaDonBan(Base):
    __tablename__ = "hoa_don_ban"

    id = Column(Integer, primary_key=True)
    so_hd = Column(String(50))

    ngay = Column(Date)

    ma_kh = Column(String(50), ForeignKey("khach_hang.ma_kh"))
    ma_nv = Column(String(50), ForeignKey("nhan_vien.ma_nv"))
    ma_kho = Column(String(20), ForeignKey("kho_hang.ma_kho"))

    tong_tien = Column(DECIMAL(18,2))
    tien_mat = Column(DECIMAL(18,2))
    tien_ck = Column(DECIMAL(18,2))
    tong_thanh_toan = Column(DECIMAL(18,2))
    no_lai = Column(DECIMAL(18,2))

    idempotency_key = Column(String(50), unique=True)

    trang_thai = Column(Enum("nhap","xac_nhan","chot","huy"))
    ngay_tao = Column(DateTime, default=datetime.now)


class HoaDonBanChiTiet(Base):
    __tablename__ = "hoa_don_ban_chi_tiet"

    id = Column(Integer, primary_key=True)
    id_hoa_don = Column(Integer, ForeignKey("hoa_don_ban.id"))
    ma_sp = Column(String(50), ForeignKey("san_pham.ma_sp"))

    so_luong = Column(DECIMAL(10,2))
    don_gia = Column(DECIMAL(18,2))
    thanh_tien = Column(DECIMAL(18,2))


# ======================
# NHẬT KÝ KHO
# ======================
class NhatKyKho(Base):
    __tablename__ = "nhat_ky_kho"

    id = Column(Integer, primary_key=True)

    ngay = Column(DateTime)

    ma_sp = Column(String(50))
    ma_kho = Column(String(20))
    ma_nv = Column(String(50))

    so_luong = Column(DECIMAL(10,2))

    loai = Column(Enum("nhap","xuat"))

    bang_tham_chieu = Column(String(50))
    id_tham_chieu = Column(Integer)

    ngay_tao = Column(DateTime, default=datetime.now)


# ======================
# THU CHI
# ======================
class ThuChi(Base):
    __tablename__ = "thu_chi"

    id = Column(Integer, primary_key=True)

    ngay = Column(DateTime, nullable=False)

    doi_tuong = Column(Enum("nhan_vien","cong_ty"))
    ma_nv = Column(String(50), ForeignKey("nhan_vien.ma_nv"))

    so_tien = Column(DECIMAL(18,2))

    loai = Column(Enum("thu","chi"))
    hinh_thuc = Column(Enum("tien_mat","chuyen_khoan"))

    noi_dung = Column(String(255))
    loai_giao_dich = Column(String(50))

    so_du_sau = Column(DECIMAL(18,2))
    so_du_ct_sau = Column(DECIMAL(18,2))

    ngay_tao = Column(DateTime, default=datetime.now)

    ma_kh = Column(String(50), nullable=True)
    ma_ncc = Column(String(50), nullable=True)

    idempotency_key = Column(String(100))
    created_by = Column(String(50))

    is_reversal = Column(Integer, default=0)
    ref_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ======================
# QUỸ NHÂN VIÊN
# ======================
class QuyNhanVienChotNgay(Base):
    __tablename__ = "quy_nhan_vien_chot_ngay"

    id = Column(Integer, primary_key=True)
    ma_nv = Column(String(50), unique=True)

    so_du = Column(DECIMAL(18,2))


# ======================
# QUỸ CÔNG TY
# ======================
class QuyCongTyChotNgay(Base):
    __tablename__ = "quy_cong_ty_chot_ngay"

    id = Column(Integer, primary_key=True)

    tien_mat = Column(DECIMAL(18,2))
    tien_ngan_hang = Column(DECIMAL(18,2))
    tong_quy = Column(DECIMAL(18,2))


# ======================
# TỒN KHO
# ======================
class TonKhoChotNgay(Base):
    __tablename__ = "ton_kho_chot_ngay"

    id = Column(Integer, primary_key=True)

    ma_kho = Column(String(20))
    ma_sp = Column(String(50))

    so_luong = Column(DECIMAL(12,2))


# ======================
# CÔNG NỢ KHÁCH HÀNG
# ======================
class CongNoKhachHang(Base):
    __tablename__ = "cong_no_khach_hang"

    id = Column(Integer, primary_key=True)

    ma_kh = Column(String(50), unique=True, nullable=False)

    so_du = Column(DECIMAL(18,2), default=0)


class CongNoKhachHangLog(Base):
    __tablename__ = "cong_no_khach_hang_log"

    id = Column(Integer, primary_key=True)
    ma_kh = Column(String(50))
    ngay = Column(DateTime)
    phat_sinh = Column(DECIMAL(18,2))
    loai = Column(String(50))
    ref_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)


# ======================
# CÔNG NỢ NCC
# ======================
class CongNoNCC(Base):
    __tablename__ = "cong_no_ncc"

    id = Column(Integer, primary_key=True)

    ma_ncc = Column(String(50), unique=True, nullable=False)

    so_du = Column(DECIMAL(18,2), default=0)


class CongNoNCCLog(Base):
    __tablename__ = "cong_no_ncc_log"

    id = Column(Integer, primary_key=True)

    ma_ncc = Column(String(50), nullable=False)

    ngay = Column(DateTime, nullable=False)

    phat_sinh = Column(DECIMAL(18,2), nullable=False)

    loai = Column(String(50))

    ref_id = Column(Integer)

    created_at = Column(DateTime, default=datetime.now)


# ======================
# GAS DƯ (FIX CHUẨN)
# ======================


class GasDu(Base):
    __tablename__ = "gas_du"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # thời điểm phát sinh
    thoi_diem = Column(DateTime, nullable=False)

    # enum match DB
    loai = Column(
        Enum(
            "nhap_du",
            "xuat_ban",
            "phat_sinh",
            "ban",
            "quy_doi_ncc",
            "dieu_chinh",
            name="gas_du_loai"
        ),
        nullable=False
    )

    ma_sp_goc = Column(String(50), nullable=False)
    ma_kho = Column(String(20), nullable=False)

    so_kg = Column(Numeric(10, 2), nullable=False)

    # 🔥 QUAN TRỌNG: đúng tên DB
    ton_sau = Column(Numeric(12, 2), nullable=False, default=0)

    id_hoa_don_ban = Column(Integer, ForeignKey("hoa_don_ban.id"), nullable=True)
    id_phieu_nhap = Column(Integer, nullable=True)

    ma_kh = Column(String(50))
    ma_nv = Column(String(50))

    ghi_chu = Column(Text)

    # 🔥 FIX LỖI 500
    ref_type = Column(String(50))
    ref_id = Column(BigInteger)

    created_at = Column(DateTime)

    __table_args__ = (
        Index("idx_sp_kho", "ma_sp_goc", "ma_kho", "id"),
        Index("idx_sp_kho_time", "ma_sp_goc", "ma_kho", "thoi_diem"),
        Index("idx_time", "thoi_diem"),
        Index("idx_hd", "id_hoa_don_ban"),
        Index("idx_gasdu_ref", "ref_id"),
    )

class HoaDonGasDuChiTiet(Base):
    __tablename__ = "hoa_don_gas_du_ct"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    id_hoa_don = Column(BigInteger)
    ma_sp_vo = Column(String(50))

    so_luong_vo = Column(Numeric(10, 2))
    quy_doi_kg = Column(Numeric(10, 2))
    tong_kg = Column(Numeric(10, 2))
    kg_ban = Column(DECIMAL(10,2))   # 🔥 THÊM
    kg_du = Column(DECIMAL(10,2))    # 🔥 THÊM
    don_gia = Column(Numeric(12, 2))
    thanh_tien = Column(Numeric(14, 2))


class HoaDonGasDu(Base):
    __tablename__ = "hoa_don_gas_du"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    ma_hd = Column(String(50))
    ma_kho = Column(String(50))

    tong_tien = Column(Numeric(14, 2), default=0)
    tien_mat = Column(Numeric(14, 2), default=0)
    tien_ck = Column(Numeric(14, 2), default=0)

    trang_thai = Column(
        Enum("nhap", "xac_nhan"),
        default="nhap"
    )

    created_at = Column(DateTime, default=datetime.utcnow)
