from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.database import get_db
from app.models import (
    ThuChi,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay
)
from app.auth_utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def dashboard(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    today = date.today()

    # =================================
    # ADMIN → QUỸ CÔNG TY
    # =================================

    if user.ma_nv == "admin":

        quy = (
            db.query(QuyCongTyChotNgay)
            .order_by(QuyCongTyChotNgay.ngay_chot.desc())
            .first()
        )

        tien_mat = quy.tien_mat if quy else 0
        tien_ngan_hang = quy.tien_ngan_hang if quy else 0
        tong_quy = quy.tong_quy if quy else 0

        thu = db.query(func.sum(ThuChi.so_tien)).filter(
            ThuChi.loai == "thu",
            func.date(ThuChi.ngay) == today
        ).scalar() or 0

        chi = db.query(func.sum(ThuChi.so_tien)).filter(
            ThuChi.loai == "chi",
            func.date(ThuChi.ngay) == today
        ).scalar() or 0

        return {
            "loai": "cong_ty",
            "tien_mat": tien_mat,
            "tien_ngan_hang": tien_ngan_hang,
            "tong_quy": tong_quy,
            "thu_hom_nay": thu,
            "chi_hom_nay": chi
        }

    # =================================
    # NHÂN VIÊN → QUỸ CÁ NHÂN
    # =================================

    else:

        quy = (
            db.query(QuyNhanVienChotNgay)
            .filter(QuyNhanVienChotNgay.ma_nv == user.ma_nv)
            .order_by(QuyNhanVienChotNgay.ngay_chot.desc())
            .first()
        )

        so_du = quy.so_du if quy else 0

        thu = db.query(func.sum(ThuChi.so_tien)).filter(
            ThuChi.ma_nv == user.ma_nv,
            ThuChi.loai == "thu",
            func.date(ThuChi.ngay) == today
        ).scalar() or 0

        chi = db.query(func.sum(ThuChi.so_tien)).filter(
            ThuChi.ma_nv == user.ma_nv,
            ThuChi.loai == "chi",
            func.date(ThuChi.ngay) == today
        ).scalar() or 0

        return {
            "loai": "nhan_vien",
            "so_du": so_du,
            "thu_hom_nay": thu,
            "chi_hom_nay": chi
        }
