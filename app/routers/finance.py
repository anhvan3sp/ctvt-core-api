from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from decimal import Decimal

from app.database import get_db
from app.models import ThuChi
from app.auth_utils import require_roles
from app.models import HoaDonBan
router = APIRouter(prefix="/finance", tags=["Finance"])


# =====================================================
# XEM QUỸ CÔNG TY (TIỀN MẶT + NGÂN HÀNG)
# =====================================================
@router.get("/quy-cong-ty")
def xem_quy_cong_ty(
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "ke_toan"]))
):

    # Tiền mặt công ty
    thu_tm = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
        ThuChi.doi_tuong == "cong_ty",
        ThuChi.hinh_thuc == "tien_mat",
        ThuChi.loai == "thu"
    ).scalar()

    chi_tm = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
        ThuChi.doi_tuong == "cong_ty",
        ThuChi.hinh_thuc == "tien_mat",
        ThuChi.loai == "chi"
    ).scalar()

    # Ngân hàng công ty
    thu_ck = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
        ThuChi.doi_tuong == "cong_ty",
        ThuChi.hinh_thuc == "chuyen_khoan",
        ThuChi.loai == "thu"
    ).scalar()

    chi_ck = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
        ThuChi.doi_tuong == "cong_ty",
        ThuChi.hinh_thuc == "chuyen_khoan",
        ThuChi.loai == "chi"
    ).scalar()

    return {
        "tien_mat_cong_ty": Decimal(str(thu_tm)) - Decimal(str(chi_tm)),
        "tien_ngan_hang_cong_ty": Decimal(str(thu_ck)) - Decimal(str(chi_ck))
    }


# =====================================================
# NỘP QUỸ NHÂN VIÊN
# =====================================================
@router.post("/nop-quy")
def nop_quy(
    so_tien: float,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["nv_dac_biet"]))
):

    so_tien = Decimal(str(so_tien))

    # Kiểm tra số dư nhân viên
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

    if so_tien > so_du:
        raise HTTPException(status_code=400, detail="Quỹ không đủ để nộp")

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

    # Cộng quỹ công ty tiền mặt
    db.add(ThuChi(
        ngay=datetime.utcnow(),
        doi_tuong="cong_ty",
        ma_nv=user.ma_nv,
        so_tien=so_tien,
        loai="thu",
        hinh_thuc="tien_mat",
        noi_dung="Nhận tiền mặt từ nhân viên"
    ))

    db.commit()

    return {"message": "Nộp quỹ thành công"}


# =====================================================
# CHỐT QUỸ (TỔNG THU CHI)
# =====================================================
@router.post("/close-day")
def close_day(
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "ke_toan"]))
):

    tong_thu = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
        ThuChi.loai == "thu"
    ).scalar()

    tong_chi = db.query(func.coalesce(func.sum(ThuChi.so_tien), 0)).filter(
        ThuChi.loai == "chi"
    ).scalar()

    return {
        "ngay": date.today(),
        "tong_thu": tong_thu,
        "tong_chi": tong_chi,
        "chenh_lech": Decimal(str(tong_thu)) - Decimal(str(tong_chi))
    }



@router.get("/cong-no/{ma_kh}")
def bao_cao_cong_no(
    ma_kh: str,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "ke_toan"]))
):

    # Tổng tiền bán
    tong_ban = db.query(
        func.coalesce(func.sum(HoaDonBan.tong_tien), 0)
    ).filter(
        HoaDonBan.ma_kh == ma_kh,
        HoaDonBan.trang_thai != "huy"
    ).scalar()

    # Tổng đã thanh toán
    tong_da_thu = db.query(
        func.coalesce(func.sum(HoaDonBan.tong_tien - HoaDonBan.no_lai), 0)
    ).filter(
        HoaDonBan.ma_kh == ma_kh,
        HoaDonBan.trang_thai != "huy"
    ).scalar()

    tong_no = Decimal(str(tong_ban)) - Decimal(str(tong_da_thu))

    return {
        "ma_kh": ma_kh,
        "tong_ban": tong_ban,
        "tong_da_thu": tong_da_thu,
        "tong_con_no": tong_no
    }

@router.get("/cong-no")
def bao_cao_cong_no_toan_bo(
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "ke_toan"]))
):

    results = db.query(
        HoaDonBan.ma_kh,
        func.coalesce(func.sum(HoaDonBan.tong_tien), 0).label("tong_ban"),
        func.coalesce(func.sum(HoaDonBan.no_lai), 0).label("tong_no")
    ).filter(
        HoaDonBan.trang_thai != "huy"
    ).group_by(
        HoaDonBan.ma_kh
    ).all()

    data = []

    for r in results:
        data.append({
            "ma_kh": r.ma_kh,
            "tong_ban": r.tong_ban,
            "tong_con_no": r.tong_no
        })

    return data
