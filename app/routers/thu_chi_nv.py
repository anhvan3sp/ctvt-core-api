from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import ThuChi
from app.auth_utils import get_current_user

router = APIRouter(prefix="/thu-chi-nv", tags=["thu_chi_nhan_vien"])


# ==============================
# Tạo thu chi
# ==============================
@router.post("/create")
def create_thu_chi_nv(
    loai: str,
    so_tien: float,
    hinh_thuc: str,
    noi_dung: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    # xác định quỹ
    if hinh_thuc == "tien_mat":
        doi_tuong = "nhan_vien"
    else:
        doi_tuong = "cong_ty"

    # lấy giao dịch gần nhất của nhân viên
    last = (
        db.query(ThuChi)
        .filter(ThuChi.ma_nv == user.ma_nv)
        .order_by(ThuChi.id.desc())
        .first()
    )

    so_du_hien_tai = last.so_du_sau if last else 0

    # tính số dư mới
    if loai == "thu":
        so_du_moi = so_du_hien_tai + so_tien
    else:
        if so_du_hien_tai < so_tien:
            raise HTTPException(
                status_code=400,
                detail="Không đủ tiền trong quỹ"
            )
        so_du_moi = so_du_hien_tai - so_tien

    thu_chi = ThuChi(
        ngay=datetime.now(),
        doi_tuong=doi_tuong,
        ma_nv=user.ma_nv,
        so_tien=so_tien,
        loai=loai,
        hinh_thuc=hinh_thuc,
        noi_dung=noi_dung,
        ngay_tao=datetime.now(),
        so_du_sau=so_du_moi
    )

    db.add(thu_chi)
    db.commit()

    return {
        "message": "Đã ghi thu chi",
        "so_du_sau": so_du_moi
    }


# ==============================
# Lấy số dư quỹ nhân viên
# ==============================
@router.get("/so-du")
def get_balance(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    last = (
        db.query(ThuChi)
        .filter(ThuChi.ma_nv == user.ma_nv)
        .order_by(ThuChi.id.desc())
        .first()
    )

    so_du = last.so_du_sau if last else 0

    return {
        "ma_nv": user.ma_nv,
        "so_du": so_du
    }


# ==============================
# Danh sách thu chi
# ==============================
@router.get("/list")
def list_thu_chi(
    limit: int = 100,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    data = (
        db.query(ThuChi)
        .filter(ThuChi.ma_nv == user.ma_nv)
        .order_by(ThuChi.id.desc())
        .limit(limit)
        .all()
    )

    return data
