from pydantic import BaseModel, Field
from typing import List
from datetime import date


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
