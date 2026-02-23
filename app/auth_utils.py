import os
from datetime import datetime, timedelta
from typing import Dict, Any

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NhanVien


# ==============================
# CONFIG
# ==============================

SECRET_KEY = os.getenv("SECRET_KEY", "ctvt_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        ma_nv: str = payload.get("sub")

        if ma_nv is None:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")

    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")

    user = db.query(NhanVien).filter(NhanVien.ma_nv == ma_nv).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User không tồn tại")

    return user.ma_nv


# ==============================
# CONFIG
# ==============================

SECRET_KEY = os.getenv("SECRET_KEY", "ctvt_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# ==============================
# PASSWORD CONTEXT
# ==============================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ==============================
# PASSWORD FUNCTIONS
# ==============================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    
    return pwd_context.verify(plain_password.strip()[:72], hashed_password)




def get_password_hash(password: str) -> str:
    """
    Hash password trước khi lưu DB.
    Cắt 72 bytes để tránh lỗi bcrypt.
    """
    return pwd_context.hash(password[:72])


# ==============================
# JWT TOKEN
# ==============================

def create_access_token(data: Dict[str, Any]) -> str:
    """
    Tạo JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt
