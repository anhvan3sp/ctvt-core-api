from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import ThuChi
from app.auth_utils import get_current_user
from app.schemas import LoaiThuChi, HinhThuc

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


@router.post("/create")
def create_thu_chi_nv(
    loai: LoaiThuChi,
    loai_giao_dich: str,
    so_tien: float,
    hinh_thuc: HinhThuc,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    # kiểm tra loại giao dịch
    if loai == "thu" and loai_giao_dich not in THU_TYPES:
        raise HTTPException(400, "loai_giao_dich không hợp lệ")

    if loai == "chi" and loai_giao_dich not in CHI_TYPES:
        raise HTTPException(400, "loai_giao_dich không hợp lệ")

    # xác định quỹ
    doi_tuong = "nhan_vien" if hinh_thuc == "tien_mat" else "cong_ty"

    # lấy số dư gần nhất
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
