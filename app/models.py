from app.database import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey, DECIMAL, func, BigInteger, Text, CheckConstraint, Index, text
from datetime import datetime
import enum

# =========================
# ENUM (CHỈ DÙNG CHO SCHEMA, KHÔNG DÙNG DB)
# =========================

class LoaiPhatSinh(str, enum.Enum):
    THU = "thu"
    CHI = "chi"


class TrangThaiPhatSinh(str, enum.Enum):
    NHAP = "nhap"
    XAC_NHAN = "xac_nhan"
    HUY = "huy"


# =========================
# MODEL PHÁT SINH (FIX CHUẨN)
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

    # 🔥 FIX QUAN TRỌNG NHẤT
    loai = Column(String(10), nullable=False, index=True)

    loai_giao_dich = Column(String(50), nullable=True)

    so_tien = Column(DECIMAL(18, 2), nullable=False)

    dien_giai = Column(Text, nullable=True)

    ref_id = Column(BigInteger, nullable=True)
    ref_type = Column(String(50), nullable=True)

    # =========================
    # CORE ERP
    # =========================

    # 🔥 FIX ENUM → STRING
    trang_thai = Column(
        String(20),
        nullable=False,
        server_default="nhap",
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
# CÁC MODEL KHÁC GIỮ NGUYÊN
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


# (các model dưới giữ nguyên y như file sếp)
