from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from decimal import Decimal

from app.database import get_db
from app.models import ThuChi

router = APIRouter(prefix="/finance", tags=["Finance"])
@router.post("/close-day")
def close_day(
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "ke_toan"]))
):


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

@router.post("/nop-quy")
def nop_quy(
    so_tien: float,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["nv_dac_biet"]))
):

    # Trừ quỹ nhân viên
    db.add(ThuChi(
        ngay=datetime.utcnow(),
        doi_tuong="nhan_vien",
        ma_nv=user.ma_nv,
        so_tien=so_tien,
        loai="chi",
        hinh_thuc="tien_mat",
        noi_dung="Nộp quỹ về công ty"
    ))

    # Tăng quỹ công ty
    db.add(ThuChi(
        ngay=datetime.utcnow(),
        doi_tuong="cong_ty",
        ma_nv=user.ma_nv,
        so_tien=so_tien,
        loai="thu",
        hinh_thuc="tien_mat",
        noi_dung="Nhận quỹ từ nhân viên"
    ))

    db.commit()

    return {"message": "Nộp quỹ thành công"}
