from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import ThuChi
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


# =====================================
# CREATE THU CHI
# =====================================

@router.post("/create")
def create_thu_chi_nv(
    data: ThuChiCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    loai = data.loai
    loai_giao_dich = data.loai_giao_dich
    so_tien = data.so_tien
    hinh_thuc = data.hinh_thuc

    if loai == "thu" and loai_giao_dich not in THU_TYPES:
        raise HTTPException(400, "loai_giao_dich không hợp lệ")

    if loai == "chi" and loai_giao_dich not in CHI_TYPES:
        raise HTTPException(400, "loai_giao_dich không hợp lệ")

    doi_tuong = "nhan_vien" if hinh_thuc == "tien_mat" else "cong_ty"

    # lấy số dư gần nhất
    last = (
        db.query(ThuChi)
        .filter(ThuChi.ma_nv == user.ma_nv)
        .order_by(ThuChi.id.desc())
        .first()
    )

    so_du_hien_tai = last.so_du_sau if last else 0

    if loai == "thu":
        so_du_moi = so_du_hien_tai + so_tien
    else:
        if so_du_hien_tai < so_tien:
            raise HTTPException(400, "Không đủ tiền trong quỹ")
        so_du_moi = so_du_hien_tai - so_tien

    thu_chi = ThuChi(
        ngay=datetime.now(),
        doi_tuong=doi_tuong,
        ma_nv=user.ma_nv,
        so_tien=so_tien,
        loai=loai,
        hinh_thuc=hinh_thuc,
        loai_giao_dich=loai_giao_dich,
        ngay_tao=datetime.now(),
        so_du_sau=so_du_moi
    )

    db.add(thu_chi)
    db.commit()

    return {
        "message": "Đã ghi thu chi",
        "so_du_sau": so_du_moi
    }


# =====================================
# SO DU QUY
# =====================================

@router.get("/so-du")
def get_so_du(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    # nếu admin -> lấy quỹ công ty
    if user.role == "admin":

        last = (
            db.query(ThuChi)
            .filter(ThuChi.doi_tuong == "cong_ty")
            .order_by(ThuChi.id.desc())
            .first()
        )

        so_du = last.so_du_sau if last else 0

        return {
            "loai_quy": "quy_cong_ty",
            "so_du": so_du
        }

    # nếu nhân viên -> lấy quỹ nhân viên
    last = (
        db.query(ThuChi)
        .filter(ThuChi.ma_nv == user.ma_nv)
        .order_by(ThuChi.id.desc())
        .first()
    )

    so_du = last.so_du_sau if last else 0

    return {
        "loai_quy": "quy_nhan_vien",
        "ma_nv": user.ma_nv,
        "so_du": so_du
    }


# =====================================
# LIST LICH SU
# =====================================

@router.get("/list")
def list_thu_chi(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    if user.role == "admin":

        data = (
            db.query(ThuChi)
            .order_by(ThuChi.id.desc())
            .limit(50)
            .all()
        )

    else:

        data = (
            db.query(ThuChi)
            .filter(ThuChi.ma_nv == user.ma_nv)
            .order_by(ThuChi.id.desc())
            .limit(50)
            .all()
        )

    result = []

    for i in data:
        result.append({
            "id": i.id,
            "ngay": i.ngay,
            "loai": i.loai,
            "loai_giao_dich": i.loai_giao_dich,
            "so_tien": i.so_tien,
            "so_du_sau": i.so_du_sau,
            "ma_nv": i.ma_nv
        })

    return result
