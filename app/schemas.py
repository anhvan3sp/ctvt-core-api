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
