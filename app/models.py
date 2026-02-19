from sqlalchemy import Column, Integer, String, Enum
from app.database import Base


class NhanVien(Base):
    __tablename__ = "nhan_vien"

    id = Column(Integer, primary_key=True, index=True)
    ma_nv = Column(String(50), unique=True, index=True, nullable=False)
    ten_nv = Column(String(255))
    vai_tro = Column(
        Enum("admin", "ke_toan", "nv_dac_biet", "nhan_vien", "ke_toan_online"),
        nullable=False
    )
    trang_thai = Column(
        Enum("hoat_dong", "ngung"),
        default="hoat_dong"
    )
    password_hash = Column(String(255))
