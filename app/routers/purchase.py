from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List

from app.database import get_db
from app.schemas import HoaDonNhapCreate, HoaDonNhapResponse
from app.auth_utils import require_roles, get_current_user
from app.models import (
    HoaDonNhap,
    TonKhoChotNgay,
    NhatKyKho,
    QuyCongTyChotNgay,
    ThuChi
)

router = APIRouter(prefix="/purchase", tags=["Purchase"])


@router.post("/")
def create_purchase(
    data: HoaDonNhapCreate,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "nv_dac_biet"]))
):

    # ❌ chặn nhân viên Công
    if user.ma_nv == "cong":
        raise HTTPException(403, "Nhan vien Cong khong duoc phep nhap hang")

    # ---- check quyền kho ----
    if user.vai_tro != "admin":
        row = db.execute(text("""
            SELECT 1 FROM nhan_vien_kho
            WHERE ma_nv = :ma_nv AND ma_kho = :ma_kho
        """), {
            "ma_nv": user.ma_nv,
            "ma_kho": data.ma_kho
        }).fetchone()

        if not row:
            raise HTTPException(403, "Khong duoc phep dung kho")

    # ---- check trùng ----
    duplicate = db.query(HoaDonNhap).filter(
        HoaDonNhap.ma_nv == user.ma_nv,
        HoaDonNhap.ma_ncc == data.ma_ncc,
        HoaDonNhap.ma_kho == data.ma_kho,
        func.date(HoaDonNhap.ngay) == func.current_date()
    ).first()

    if duplicate and not data.force_create:
        return {
            "warning": True,
            "message": "Hoa don da ton tai trong ngay"
        }

    # =========================
    # TRANSACTION
    # =========================
    with db.begin():

        # =========================
        # LOCK QUỸ CÔNG TY
        # =========================
        quy_ct = db.query(QuyCongTyChotNgay)\
            .with_for_update()\
            .first()

        if not quy_ct:
            raise HTTPException(400, "Chua co quy cong ty")

        tong_tien = 0

        # =========================
        # XỬ LÝ TỪNG ITEM
        # =========================
        for item in data.items:

            so_luong = item.so_luong
            gia = item.don_gia
            thanh_tien = so_luong * gia

            tong_tien += thanh_tien

            # =========================
            # LOCK TỒN KHO
            # =========================
            ton = db.query(TonKhoChotNgay)\
                .filter_by(ma_kho=data.ma_kho, ma_sp=item.ma_sp)\
                .with_for_update()\
                .first()

            if not ton:
                raise HTTPException(400, f"Chua co ton kho {item.ma_sp}")

            # =========================
            # CỘNG KHO
            # =========================
            ton.so_luong += so_luong

            # =========================
            # LOG KHO
            # =========================
            db.add(NhatKyKho(
                ma_kho=data.ma_kho,
                ma_sp=item.ma_sp,
                loai="nhap",
                so_luong=so_luong,
                ma_nv=user.ma_nv
            ))

        # =========================
        # TRỪ TIỀN CÔNG TY
        # =========================
        if data.hinh_thuc == "tien_mat":
            if quy_ct.tien_mat < tong_tien:
                raise HTTPException(400, "Khong du tien mat")
            quy_ct.tien_mat -= tong_tien
        else:
            if quy_ct.tien_ngan_hang < tong_tien:
                raise HTTPException(400, "Khong du tien CK")
            quy_ct.tien_ngan_hang -= tong_tien

        quy_ct.tong_quy = quy_ct.tien_mat + quy_ct.tien_ngan_hang

        # =========================
        # LOG TIỀN
        # =========================
        db.add(ThuChi(
            ma_nv=user.ma_nv,
            loai="chi",
            loai_giao_dich="nhap_hang",
            so_tien=tong_tien,
            hinh_thuc=data.hinh_thuc,
            so_du_ct_sau=quy_ct.tong_quy
        ))

        # =========================
        # TẠO HÓA ĐƠN
        # =========================
        hoa_don = HoaDonNhap(
            ma_nv=user.ma_nv,
            ma_ncc=data.ma_ncc,
            ma_kho=data.ma_kho,
            tong_tien=tong_tien
        )

        db.add(hoa_don)

    return {
        "message": "Nhap hang OK",
        "tong_tien": tong_tien
    }


# =========================
# DANH SÁCH
# =========================
@router.get("/", response_model=List[HoaDonNhapResponse])
def get_purchase_list(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return db.query(HoaDonNhap).order_by(HoaDonNhap.id.desc()).all()
