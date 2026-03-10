from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import ThuChi
from app.auth_utils import get_current_user

router = APIRouter(prefix="/thu-chi-nv", tags=["thu_chi_nhan_vien"])


@router.post("/create")
def create_thu_chi_nv(
    loai: str,
    so_tien: float,
    hinh_thuc: str,
    noi_dung: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    thu_chi = ThuChi(
        ngay = datetime.now(),
        doi_tuong = "nhan_vien",
        ma_nv = user.ma_nv,
        so_tien = so_tien,
        loai = loai,
        hinh_thuc = hinh_thuc,
        noi_dung = noi_dung
    )

    db.add(thu_chi)
    db.commit()

    return {
        "message":"Đã ghi thu chi",
        "ma_nv":user.ma_nv
    }
