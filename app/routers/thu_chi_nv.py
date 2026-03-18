from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date

from app.database import get_db
from app.models import ThuChi, QuyNhanVienChotNgay, QuyCongTyChotNgay
from app.auth_utils import get_current_user
from app.schemas import ThuChiCreate

router = APIRouter(prefix="/thu-chi-nv", tags=["thu_chi_nhan_vien"])


THU_TYPES = [
    "khach_tra_no",
    "khach_dat_hang",
    "cho_hang_thue",
    "thu_khac"
]

CHI_TYPES = [
    "do_dau",
    "sua_xe",
    "dang_kiem",
    "tien_doi",
    "chi_khac"
]


# ====================================================
# CREATE THU CHI
# ====================================================

@router.post("/create")
def create_thu_chi_nv(
    data: ThuChiCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    if data.loai == "thu" and data.loai_giao_dich not in THU_TYPES:
        raise HTTPException(400, "loai_giao_dich không hợp lệ")

    if data.loai == "chi" and data.loai_giao_dich not in CHI_TYPES:
        raise HTTPException(400, "loai_giao_dich không hợp lệ")

    last = (
        db.query(ThuChi)
        .filter(ThuChi.ma_nv == user.ma_nv)
        .order_by(ThuChi.id.desc())
        .first()
    )

    so_du_hien_tai = last.so_du_sau if last else 0

    if data.loai == "thu":
        so_du_moi = so_du_hien_tai + data.so_tien
    else:

        if so_du_hien_tai < data.so_tien:
            raise HTTPException(400, "Không đủ tiền")

        so_du_moi = so_du_hien_tai - data.so_tien

    thu_chi = ThuChi(
        ngay=datetime.now(),
        ma_nv=user.ma_nv,
        doi_tuong="nhan_vien",
        loai=data.loai,
        loai_giao_dich=data.loai_giao_dich,
        so_tien=data.so_tien,
        hinh_thuc=data.hinh_thuc,
        so_du_sau=so_du_moi,
        ngay_tao=datetime.now()
    )

    db.add(thu_chi)
    db.commit()

    return {
        "message": "ok",
        "so_du": so_du_moi
    }


# ====================================================
# DASHBOARD
# ====================================================

@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    today = date.today()

    # ===============================
    # ADMIN → QUỸ CÔNG TY
    # ===============================

    if user.ma_nv == "admin":

        last_quy = (
            db.query(QuyCongTyChotNgay)
            .order_by(QuyCongTyChotNgay.ngay_chot.desc())
            .first()
        )

        quy_hien_tai = last_quy.tong_quy if last_quy else 0

        thu = db.query(func.sum(ThuChi.so_tien)).filter(
            ThuChi.loai == "thu",
            func.date(ThuChi.ngay) == today
        ).scalar() or 0

        chi = db.query(func.sum(ThuChi.so_tien)).filter(
            ThuChi.loai == "chi",
            func.date(ThuChi.ngay) == today
        ).scalar() or 0


    # ===============================
    # NHÂN VIÊN → QUỸ CÁ NHÂN
    # ===============================

    else:

        last_quy = (
            db.query(QuyNhanVienChotNgay)
            .filter(QuyNhanVienChotNgay.ma_nv == user.ma_nv)
            .order_by(QuyNhanVienChotNgay.ngay_chot.desc())
            .first()
        )

        quy_hien_tai = last_quy.so_du if last_quy else 0

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
        "quy_hien_tai": quy_hien_tai,
        "thu_hom_nay": thu,
        "chi_hom_nay": chi
    }
