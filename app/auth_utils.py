import os
from datetime import datetime, timedelta
from typing import Dict, Any

from jose import jwt
from passlib.context import CryptContext


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
    """
    So sánh password người dùng nhập với password đã hash trong DB.
    Bcrypt chỉ xử lý tối đa 72 bytes -> cần cắt trước khi verify.
    """
    if not plain_password or not hashed_password:
        return False

    return pwd_context.verify(plain_password[:72], hashed_password)


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
