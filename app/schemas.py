from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from enum import Enum






class TonKhoDauKy(BaseModel):
    ma_sp: str
    ma_kho: str
    so_luong: float


class QuyNhanVienDauKy(BaseModel):
    ma_nv: str
    so_du: float


class CongNoKhachHangDauKy(BaseModel):
    ma_kh: str
    so_no: float


class CongNoNCCDauKy(BaseModel):
    ma_ncc: str
    so_no: float


class KhoiTaoDauKyRequest(BaseModel):

    ngay: str

    ton_kho: List[TonKhoDauKy]

    quy_nhan_vien: List[QuyNhanVienDauKy]

    quy_cong_ty: float

    cong_no_khach: List[CongNoKhachHangDauKy]

    cong_no_ncc: List[CongNoNCCDauKy]

class DebtDetailResponse(BaseModel):
    ma_hoa_don: str
    ngay: date
    tong_tien: float
    da_tra: float
    con_no: float

    class Config:
        from_attributes = True
# =====================================================
# ENUMS (KHÓA GIÁ TRỊ)
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
    ngay: date
    ma_ncc: str
    ma_kho: str
    tien_mat: Decimal = Decimal("0")
    tien_ck: Decimal = Decimal("0")
    items: List[HoaDonNhapItemCreate]
    tong_tien: float
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

class CustomerBase(BaseModel):
    ma_kh: str
    ten_cua_hang: str
    ten_cua_hang_chi_tiet: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    dia_chi: Optional[str] = None
    ma_so_thue: Optional[str] = None
    ghi_chu: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int

    class Config:
        orm_mode = True
