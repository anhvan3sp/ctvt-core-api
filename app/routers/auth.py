from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NhanVien
from app.auth_utils import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login theo chuẩn OAuth2.
    Swagger sẽ gửi username + password dạng form-data.
    """

    user = db.query(NhanVien).filter(
        NhanVien.ma_nv == form_data.username,
        NhanVien.trang_thai == "hoat_dong"
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Sai mã nhân viên")

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Sai mật khẩu")

    access_token = create_access_token(
        data={
            "sub": user.ma_nv,
            "role": user.vai_tro
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
