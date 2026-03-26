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


# ⚠️ KHÔNG dùng Enum cho loai_giao_dich (để khớp DB thu_chi)
# class LoaiGiaoDich ...


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

    loai = Column(
        Enum(LoaiPhatSinh),
        nullable=False,
        index=True
    )

    # 🔥 FIX: dùng String để khớp DB thu_chi
    loai_giao_dich = Column(String(50), nullable=True)

    so_tien = Column(DECIMAL(18, 2), nullable=False)

    dien_giai = Column(Text, nullable=True)

    ref_id = Column(BigInteger, nullable=True)
    ref_type = Column(String(50), nullable=True)

    # =========================
    # CORE ERP
    # =========================

    trang_thai = Column(
        Enum(TrangThaiPhatSinh),
        nullable=False,
        server_default=text("'nhap'"),
        index=True
    )

    id_thu_chi = Column(BigInteger, nullable=True, index=True)

    id_thu_chi_dao = Column(BigInteger, nullable=True, index=True)

    # 🔥 KHÔNG unique (tránh crash)
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
    ngay_tao = Column(DateTime, default=datetime.utcnow)


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
    ngay_tao = Column(DateTime, default=datetime.utcnow)


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

    ngay_tao = Column(DateTime, default=datetime.utcnow)


# ======================
# THU CHI (FIX KHỚP DB)
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

    ngay_tao = Column(DateTime, default=datetime.utcnow)

    ma_kh = Column(String(50), nullable=True)
    ma_ncc = Column(String(50), nullable=True)

    idempotency_key = Column(String(100))
    created_by = Column(String(50))

    # 🔥 thêm để support reversal chuẩn
    is_reversal = Column(Integer, default=0)
    ref_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime)


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
    created_at = Column(DateTime, default=datetime.utcnow)


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

    created_at = Column(DateTime, default=datetime.utcnow)
