from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NhanVien
from app.schemas import LoginRequest, LoginResponse
from app.auth_utils import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(NhanVien).filter(
        NhanVien.ma_nv == data.ma_nv,
        NhanVien.trang_thai == "hoat_dong"
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Sai mã nhân viên")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Sai mật khẩu")

    token = create_access_token({
        "sub": user.ma_nv,
        "role": user.vai_tro
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "ma_nv": user.ma_nv,
        "vai_tro": user.vai_tro
    }
