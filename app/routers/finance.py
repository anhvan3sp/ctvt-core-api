from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime

from app.database import get_db
from app.models import ThuChi
from app.auth_utils import require_roles, get_current_user
from app.schemas import ThuChiCreate, ThuChiResponse, NopQuyRequest

router = APIRouter(prefix="/finance", tags=["Finance"])


# =====================================================
# TẠO THU CHI THỦ CÔNG
# =====================================================
@router.post("/thu-chi", response_model=ThuChiResponse)
def create_thu_chi(
    data: ThuChiCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    - Admin, kế toán: ghi cho công ty
    - nv_dac_biet: ghi cho chính mình
    """

    doi_tuong = data.doi_tuong

    if user.vai_tro == "nv_dac_biet":
        doi_tuong = "nhan_vien"

    thu_chi = ThuChi(
        ngay=data.ngay,
        doi_tuong=doi_tuong,
        ma_nv=user.ma_nv,
        so_tien=data.so_tien,
        loai=data.loai,
        hinh_thuc=data.hinh_thuc,
        noi_dung=data.noi_dung
    )

    db.add(thu_chi)
    db.commit()
    db.refresh(thu_chi)

    return thu_chi


# =====================================================
# DANH SÁCH THU CHI
# =====================================================
@router.get("/thu-chi", response_model=list[ThuChiResponse])
def get_thu_chi_list(
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "ke_toan"]))
):
    return db.query(ThuChi).order_by(ThuChi.id.desc()).all()


# =====================================================
# NỘP QUỸ (nv_dac_biet → công ty)
# =====================================================
@router.post("/nop-quy")
def nop_quy(
    data: NopQuyRequest,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["nv_dac_biet"]))
):

    if data.so_tien <= 0:
        raise HTTPException(status_code=400, detail="Số tiền phải > 0")

    # Tính số dư nhân viên
    thu = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
        ThuChi.doi_tuong == "nhan_vien",
        ThuChi.ma_nv == user.ma_nv,
        ThuChi.loai == "thu"
    ).scalar()

    chi = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
        ThuChi.doi_tuong == "nhan_vien",
        ThuChi.ma_nv == user.ma_nv,
        ThuChi.loai == "chi"
    ).scalar()

    so_du = Decimal(str(thu)) - Decimal(str(chi))

    if data.so_tien > so_du:
        raise HTTPException(status_code=400, detail="Quỹ không đủ")

    # Trừ quỹ nhân viên
    db.add(ThuChi(
        ngay=datetime.utcnow(),
        doi_tuong="nhan_vien",
        ma_nv=user.ma_nv,
        so_tien=data.so_tien,
        loai="chi",
        hinh_thuc=data.hinh_thuc,
        noi_dung="Nộp quỹ về công ty"
    ))

    # Cộng quỹ công ty
    db.add(ThuChi(
        ngay=datetime.utcnow(),
        doi_tuong="cong_ty",
        ma_nv=user.ma_nv,
        so_tien=data.so_tien,
        loai="thu",
        hinh_thuc=data.hinh_thuc,
        noi_dung="Nhận tiền từ nhân viên"
    ))

    db.commit()

    return {"message": "Nộp quỹ thành công"}


# =====================================================
# QUỸ CÔNG TY REALTIME
# =====================================================
@router.get("/quy-cong-ty")
def xem_quy_cong_ty(
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "ke_toan"]))
):

    tong = db.query(
        func.coalesce(
            func.sum(
                func.case(
                    (ThuChi.loai == "thu", ThuChi.so_tien),
                    else_=-ThuChi.so_tien
                )
            ), 0
        )
    ).filter(
        ThuChi.doi_tuong == "cong_ty"
    ).scalar()

    return {"quy_cong_ty": Decimal(str(tong))}


# =====================================================
# QUỸ NHÂN VIÊN (CHÍNH MÌNH)
# =====================================================
@router.get("/quy-nhan-vien")
def xem_quy_nhan_vien(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    tong = db.query(
        func.coalesce(
            func.sum(
                func.case(
                    (ThuChi.loai == "thu", ThuChi.so_tien),
                    else_=-ThuChi.so_tien
                )
            ), 0
        )
    ).filter(
        ThuChi.doi_tuong == "nhan_vien",
        ThuChi.ma_nv == user.ma_nv
    ).scalar()

    return {"quy_nhan_vien": Decimal(str(tong))}
