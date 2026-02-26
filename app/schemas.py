from pydantic import BaseModel, Field
from typing import List
from datetime import date
from decimal import Decimal
from datetime import datetime

class LoginRequest(BaseModel):
    ma_nv: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    ma_nv: str
    vai_tro: str



class HoaDonNhapItemCreate(BaseModel):
    ma_sp: str
    so_luong: float = Field(..., gt=0)
    don_gia: float = Field(..., gt=0)

class HoaDonNhapResponse(BaseModel):
    id: int
    ngay: date
    ma_ncc: str
    ma_nv: str
    ma_kho: str
    tong_tien: float

    class Config:
        from_attributes = True

class HoaDonNhapCreate(BaseModel):
    ngay: date
    ma_ncc: str
    ma_kho: str
    tien_mat: float = 0
    tien_ck: float = 0
    items: List[HoaDonNhapItemCreate]

class HoaDonBanItemCreate(BaseModel):
    ma_sp: str
    so_luong: float = Field(..., gt=0)
    don_gia: float = Field(..., gt=0)


class HoaDonBanCreate(BaseModel):
    ngay: date
    ma_kh: str
    ma_kho: str
    tien_mat: float = 0
    tien_ck: float = 0
    items: List[HoaDonBanItemCreate]




# ==============================
# THU CHI
# ==============================

class ThuChiCreate(BaseModel):
    ngay: datetime
    doi_tuong: str  # "cong_ty" hoặc "nhan_vien"
    so_tien: Decimal
    loai: str       # "thu" hoặc "chi"
    hinh_thuc: str  # "tien_mat" hoặc "chuyen_khoan"
    noi_dung: str


class ThuChiResponse(ThuChiCreate):
    id: int
    ma_nv: str | None = None

    class Config:
        from_attributes = True


class NopQuyRequest(BaseModel):
    so_tien: Decimal
    hinh_thuc: str  # "tien_mat" hoặc "chuyen_khoan"
