from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


# =====================================================
# ENUMS
# =====================================================

class LoaiThuChi(str, Enum):
    thu = "thu"
    chi = "chi"


class HinhThuc(str, Enum):
    tien_mat = "tien_mat"
    chuyen_khoan = "chuyen_khoan"


class DoiTuong(str, Enum):
    cong_ty = "cong_ty"
    nhan_vien = "nhan_vien"


# =====================================================
# AUTH
# =====================================================

class LoginRequest(BaseModel):
    ma_nv: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    ma_nv: str
    vai_tro: str


# =====================================================
# MASTER DATA
# =====================================================

class SupplierBase(BaseModel):
    ma_ncc: str
    ten_ncc: str


class SupplierResponse(SupplierBase):
    id: int
    class Config:
        orm_mode = True


class WarehouseBase(BaseModel):
    ma_kho: str
    ten_kho: str


class WarehouseResponse(WarehouseBase):
    id: int
    class Config:
        orm_mode = True


class ProductBase(BaseModel):
    ma_sp: str
    ten_sp: str


class ProductResponse(ProductBase):
    id: int
    class Config:
        orm_mode = True


# =====================================================
# HÓA ĐƠN NHẬP
# =====================================================

class HoaDonNhapItemCreate(BaseModel):
    ma_sp: str
    so_luong: Decimal = Field(..., gt=0)
    don_gia: Decimal = Field(..., gt=0)


class HoaDonNhapCreate(BaseModel):
    ma_ncc: str
    ma_kho: str
    tien_mat: Decimal = Decimal("0")
    tien_ck: Decimal = Decimal("0")
    items: List[HoaDonNhapItemCreate]
    force_create: bool = False


class HoaDonNhapResponse(BaseModel):
    id: int
    ngay: date
    ma_ncc: str
    ma_nv: str
    ma_kho: str
    tong_tien: Decimal

    class Config:
        orm_mode = True


# =====================================================
# HÓA ĐƠN BÁN
# =====================================================

class HoaDonBanItemCreate(BaseModel):
    ma_sp: str
    so_luong: Decimal = Field(..., gt=0)
    don_gia: Decimal = Field(..., gt=0)


class HoaDonBanCreate(BaseModel):
    ngay: date
    ma_kh: str
    ma_kho: str
    tien_mat: Decimal = Decimal("0")
    tien_ck: Decimal = Decimal("0")
    items: List[HoaDonBanItemCreate]


class HoaDonBanResponse(BaseModel):
    id: int
    ngay: date
    ma_kh: str
    ma_nv: str
    ma_kho: str
    tong_tien: Decimal

    class Config:
        orm_mode = True


# =====================================================
# THU CHI
# =====================================================

class ThuChiCreate(BaseModel):
    ngay: datetime
    doi_tuong: DoiTuong
    so_tien: Decimal
    loai: LoaiThuChi
    hinh_thuc: HinhThuc


class ThuChiResponse(ThuChiCreate):
    id: int
    ma_nv: Optional[str] = None

    class Config:
        orm_mode = True


# =====================================================
# NỘP QUỸ
# =====================================================

class NopQuyRequest(BaseModel):
    so_tien: Decimal
    hinh_thuc: HinhThuc


# =====================================================
# KHÁCH HÀNG
# =====================================================

class CustomerBase(BaseModel):
    ma_kh: str
    ten_cua_hang: str

class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int

    class Config:
        orm_mode = True


# =====================================================
# 🔥 ĐẦU KỲ
# =====================================================

class TonKhoItem(BaseModel):
    ma_kho: str
    ma_sp: str
    so_luong: float


class QuyNVItem(BaseModel):
    ma_nv: str
    so_du: float


class QuyCongTyItem(BaseModel):
    tien_mat: float = 0
    tien_ngan_hang: float = 0


class CongNoKhachItem(BaseModel):
    ma_kh: str
    so_du: float


class CongNoNCCItem(BaseModel):
    ma_ncc: str
    so_du: float


class DauKyPayload(BaseModel):
    ton_kho: List[TonKhoItem]
    quy_nhan_vien: List[QuyNVItem]
    quy_cong_ty: QuyCongTyItem

    cong_no_khach: List[CongNoKhachItem] = Field(default_factory=list)
    cong_no_ncc: List[CongNoNCCItem] = Field(default_factory=list)
