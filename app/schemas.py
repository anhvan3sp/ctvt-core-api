from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pydantic import field_validator, model_validator
from typing import Optional, Literal

# =====================================================
# 🔥 ĐẦU KỲ (GIỮ FILE CŨ + FIX)
# =====================================================

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


class QuyCongTyDauKy(BaseModel):
    tien_mat: float = 0
    tien_ngan_hang: float = 0


class KhoiTaoDauKyRequest(BaseModel):
    ngay: Optional[str] = None
    ton_kho: List[TonKhoDauKy]
    quy_nhan_vien: List[QuyNhanVienDauKy]
    quy_cong_ty: QuyCongTyDauKy
    cong_no_khach: List[CongNoKhachHangDauKy] = Field(default_factory=list)
    cong_no_ncc: List[CongNoNCCDauKy] = Field(default_factory=list)


# =====================================================
# 🔥 CÔNG NỢ CHI TIẾT (GIỮ NGUYÊN)
# =====================================================

class DebtDetailResponse(BaseModel):
    ma_hoa_don: str
    ngay: date
    tong_tien: float
    da_tra: float
    con_no: float

    class Config:
        from_attributes = True


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


# 🔥 NEW ENUM (PHÁT SINH)

class TrangThaiPhatSinh(str, Enum):
    nhap = "nhap"
    xac_nhan = "xac_nhan"
    huy = "huy"


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
    force: Optional[bool] = False


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
    force: Optional[bool] = False


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
# THU CHI (GIỮ NGUYÊN)
# =====================================================

class ThuChiCreate(BaseModel):
    loai: Literal["thu", "chi"]
    loai_giao_dich: str
    so_tien: float
    hinh_thuc: Literal["tien_mat", "chuyen_khoan"]

    ma_kh: Optional[str] = None
    ma_ncc: Optional[str] = None

    noi_dung: Optional[str] = None
    idempotency_key: Optional[str] = None
    force: Optional[bool] = False

    @field_validator("so_tien")
    @classmethod
    def validate_so_tien(cls, v):
        if v <= 0:
            raise ValueError("Số tiền phải > 0")
        return v

    @model_validator(mode="after")
    def validate_logic(self):

        if self.loai_giao_dich == "nop_tien":
            if self.loai != "chi":
                raise ValueError("Nộp tiền phải là chi")

        if self.loai_giao_dich == "nop_them":
            if self.loai != "thu":
                raise ValueError("Nộp thêm phải là thu")

        return self


class ThuChiResponse(ThuChiCreate):
    id: int
    ma_nv: Optional[str] = None

    class Config:
        orm_mode = True


# =====================================================
# 🔥 PHÁT SINH (NEW - CORE ERP)
# =====================================================

class PhatSinhCreate(BaseModel):
    ngay: date
    loai: Literal["thu", "chi"]
    loai_giao_dich: str
    so_tien: float
    dien_giai: Optional[str] = None
    force: bool = False  
    @field_validator("so_tien")
    @classmethod
    def validate_so_tien(cls, v):
        if v <= 0:
            raise ValueError("Số tiền phải > 0")
        return v


class PhatSinhConfirm(BaseModel):
    id: int


class PhatSinhCancel(BaseModel):
    id: int


class PhatSinhResponse(BaseModel):
    id: int
    ma_nv: str
    ngay: date
    loai: str
    loai_giao_dich: Optional[str]
    so_tien: float
    dien_giai: Optional[str]
    trang_thai: TrangThaiPhatSinh

    id_thu_chi: Optional[int]
    id_thu_chi_dao: Optional[int]

    created_at: Optional[datetime]

    class Config:
        orm_mode = True


# =====================================================
# NỘP QUỸ
# =====================================================

class NopQuyRequest(BaseModel):
    so_tien: Decimal
    hinh_thuc: HinhThuc


# =====================================================
# KHÁCH HÀNG (GIỮ NGUYÊN)
# =====================================================

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
