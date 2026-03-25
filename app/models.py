from app.database import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey, DECIMAL
from datetime import datetime


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

    idempotency_key = Column(String(50), unique=True)  # ✅ THÊM

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

    ngay_tao = Column(DateTime, default=datetime.utcnow)

    # giữ nhưng không dùng
    ma_kh = Column(String(50), nullable=True)
    ma_ncc = Column(String(50), nullable=True)

    # 🔥 FIX
    idempotency_key = Column(String(100))
    created_by = Column(String(50))

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
# TỒN KHO (CURRENT)
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
    ref_id = Column(Integer)  # ✅ THÊM DÒNG NÀY
    created_at = Column(DateTime, default=datetime.utcnow)
# ======================
# CÔNG NỢ NHÀ CUNG CẤP
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



