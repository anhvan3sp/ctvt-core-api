from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date
import uuid

from app.db.session import get_db
from app.models.phat_sinh import PhatSinh, TrangThaiPhatSinh
from app.schemas.phat_sinh import (
    PhatSinhCreate,
    PhatSinhConfirm,
    PhatSinhCancel
)

# ⚠️ import API cũ (service hoặc call nội bộ)
from app.services.thu_chi_service import create_thu_chi

router = APIRouter(prefix="/phat-sinh", tags=["PhatSinh"])
