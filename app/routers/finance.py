from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from decimal import Decimal

from app.database import get_db
from app.models import ThuChi

router = APIRouter(prefix="/finance", tags=["Finance"])

@router.post("/close-day")
def close_day(db: Session = Depends(get_db)):

    tong_thu = db.query(
        func.coalesce(func.sum(ThuChi.so_tien), 0)
    ).filter(
        ThuChi.loai == "thu"
    ).scalar()

    tong_chi = db.query(
        func.coalesce(func.sum(ThuChi.so_tien), 0)
    ).filter(
        ThuChi.loai == "chi"
    ).scalar()

    return {
        "ngay": date.today(),
        "tong_thu": tong_thu,
        "tong_chi": tong_chi,
        "chenh_lech": Decimal(str(tong_thu)) - Decimal(str(tong_chi))
    }
