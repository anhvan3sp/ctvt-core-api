from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal


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
        from_attributes = True


class WarehouseBase(BaseModel):
    ma_kho: str
    ten_kho: str


class WarehouseResponse(WarehouseBase):
    id: int

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    ma_sp: str
    ten_sp: str


class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True


# =====================================================
# HÓA ĐƠN NHẬP
# =====================================================

class HoaDonNhapItemCreate(BaseModel):
    ma_sp: str
    so_luong: Decimal = Field(..., gt=0)
    don_gia: Decimal = Field(..., gt=0)


class HoaDonNhapCreate(BaseModel):
    ngay: date
    ma_ncc: str
    ma_kho: str
    tien_mat: Decimal = 0
    tien_ck: Decimal = 0
    items: List[HoaDonNhapItemCreate]


class HoaDonNhapResponse(BaseModel):
    id: int
    ngay: date
    ma_ncc: str
    ma_nv: str
    ma_kho: str
    tong_tien: Decimal

    class Config:
        from_attributes = True


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
    tien_mat: Decimal = 0
    tien_ck: Decimal = 0
    items: List[HoaDonBanItemCreate]


class HoaDonBanResponse(BaseModel):
    id: int
    ngay: date
    ma_kh: str
    ma_nv: str
    ma_kho: str
    tong_tien: Decimal

    class Config:
        from_attributes = True


# =====================================================
# THU CHI
# =====================================================

class ThuChiCreate(BaseModel):
    ngay: datetime
    doi_tuong: str  # "cong_ty" hoặc "nhan_vien"
    so_tien: Decimal
    loai: str       # "thu" hoặc "chi"
    hinh_thuc: str  # "tien_mat" hoặc "chuyen_khoan"
    noi_dung: str


class ThuChiResponse(ThuChiCreate):
    id: int
    ma_nv: Optional[str] = None

    class Config:
        from_attributes = True


# =====================================================
# NỘP QUỸ
# =====================================================

class NopQuyRequest(BaseModel):
    so_tien: Decimal
    hinh_thuc: str  # "tien_mat" hoặc "chuyen_khoan"
