from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta

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
    "nop_tien",   # 👈 thêm
    "chi_khac"
]


@router.post("/create")
def create_thu_chi_nv(
    data: ThuChiCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    # validate
    if data.loai == "thu" and data.loai_giao_dich not in THU_TYPES:
        raise HTTPException(400, "loai_giao_dich không hợp lệ")

    if data.loai == "chi" and data.loai_giao_dich not in CHI_TYPES:
        raise HTTPException(400, "loai_giao_dich không hợp lệ")

    # lấy số dư
    last = (
        db.query(ThuChi)
        .filter(ThuChi.ma_nv == user.ma_nv)
        .order_by(ThuChi.id.desc())
        .first()
    )

    so_du_hien_tai = float(last.so_du_sau) if last else 0

    # ==============================
    # CASE: NỘP TIỀN
    # ==============================
    if data.loai == "chi" and data.loai_giao_dich == "nop_tien":

        if so_du_hien_tai < data.so_tien:
            raise HTTPException(400, "Không đủ tiền")

        so_du_moi = so_du_hien_tai - data.so_tien

        # 1. TRỪ QUỸ NHÂN VIÊN
        chi_nv = ThuChi(
            ngay=datetime.now(),
            ma_nv=user.ma_nv,
            doi_tuong="nhan_vien",
            loai="chi",
            loai_giao_dich="nop_tien",
            so_tien=data.so_tien,
            hinh_thuc=data.hinh_thuc,
            so_du_sau=so_du_moi,
            ngay_tao=datetime.now(),
            noi_dung="Nộp tiền về công ty"
        )

        db.add(chi_nv)

        # 2. CỘNG QUỸ CÔNG TY
        thu_ct = ThuChi(
            ngay=datetime.now(),
            ma_nv=user.ma_nv,
            doi_tuong="cong_ty",
            loai="thu",
            loai_giao_dich="nop_tien",
            so_tien=data.so_tien,
            hinh_thuc=data.hinh_thuc,
            ngay_tao=datetime.now(),
            noi_dung=f"{user.ma_nv} nộp tiền về công ty"
        )

        db.add(thu_ct)

        db.commit()

        return {
            "message": "Nộp tiền thành công",
            "so_du": so_du_moi
        }

    # ==============================
    # CASE BÌNH THƯỜNG
    # ==============================

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
