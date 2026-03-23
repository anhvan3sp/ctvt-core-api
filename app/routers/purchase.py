from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal
from datetime import datetime

from app.database import get_db
from app.schemas import HoaDonNhapCreate
from app.auth_utils import require_roles
from app.models import (
    HoaDonNhap,
    TonKhoChotNgay,
    NhatKyKho,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    ThuChi,
    NhaCungCap
)

router = APIRouter(prefix="/purchase", tags=["Purchase"])


def to_decimal(val):
    return Decimal(str(val or 0))


@router.post("/")
def create_purchase(
    data: HoaDonNhapCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nv_dac_biet"]))
):

    try:

        quy_nv = db.query(QuyNhanVienChotNgay)\
            .filter_by(ma_nv=user.ma_nv)\
            .with_for_update()\
            .first()

        quy_ct = db.query(QuyCongTyChotNgay)\
            .with_for_update()\
            .first()

        ncc = db.query(NhaCungCap)\
            .filter_by(ma_ncc=data.ma_ncc)\
            .with_for_update()\
            .first()

        if not quy_ct or not ncc:
            raise HTTPException(400, "Thiếu dữ liệu")

        tong_tien = Decimal("0")

        # ===== KHO =====
        for item in data.items:
            ton = db.query(TonKhoChotNgay)\
                .filter_by(ma_kho=data.ma_kho, ma_sp=item.ma_sp)\
                .with_for_update()\
                .first()

            if not ton:
                raise HTTPException(400, "Chưa có tồn kho")

            ton.so_luong += item.so_luong

            db.add(NhatKyKho(
                ma_kho=data.ma_kho,
                ma_sp=item.ma_sp,
                loai="nhap",
                so_luong=item.so_luong,
                ma_nv=user.ma_nv,
                ngay=datetime.now()
            ))

            tong_tien += Decimal(item.so_luong) * Decimal(item.don_gia)

        tien_mat = to_decimal(data.tien_mat)
        tien_ck = to_decimal(data.tien_ck)

        if tien_mat + tien_ck > tong_tien:
            raise HTTPException(400, "Tiền vượt tổng")

        no_moi = tong_tien - tien_mat - tien_ck

        # ===== TIỀN =====
        if user.ma_nv == "admin":

            if tien_mat > 0:
                if quy_ct.tien_mat < tien_mat:
                    raise HTTPException(400, "Thiếu tiền mặt")
                quy_ct.tien_mat -= tien_mat

            if tien_ck > 0:
                if quy_ct.tien_ngan_hang < tien_ck:
                    raise HTTPException(400, "Thiếu CK")
                quy_ct.tien_ngan_hang -= tien_ck

        else:

            if not quy_nv:
                raise HTTPException(400, "Chưa có quỹ NV")

            if tien_mat + tien_ck > quy_nv.so_du:
                raise HTTPException(400, "Không đủ tiền NV")

            quy_nv.so_du -= (tien_mat + tien_ck)

        # ===== CÔNG NỢ =====
        if no_moi > 0:
            ncc.cong_no = (ncc.cong_no or 0) + no_moi

        quy_ct.tong_quy = (quy_ct.tien_mat or 0) + (quy_ct.tien_ngan_hang or 0)

        # ===== LOG TIỀN (CHUẨN) =====
        if tien_mat > 0:
            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong="cong_ty",
                ma_nv=user.ma_nv,
                so_tien=tien_mat,
                loai="chi",
                hinh_thuc="tien_mat",
                loai_giao_dich="nhap_hang",
                so_du_ct_sau=quy_ct.tong_quy
            ))

        if tien_ck > 0:
            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong="cong_ty",
                ma_nv=user.ma_nv,
                so_tien=tien_ck,
                loai="chi",
                hinh_thuc="chuyen_khoan",
                loai_giao_dich="nhap_hang",
                so_du_ct_sau=quy_ct.tong_quy
            ))

        # ===== HÓA ĐƠN =====
        db.add(HoaDonNhap(
            ngay=datetime.now(),
            ma_nv=user.ma_nv,
            ma_ncc=data.ma_ncc,
            ma_kho=data.ma_kho,
            tong_tien=tong_tien
        ))

        db.commit()

        return {
            "message": "OK",
            "tong_tien": float(tong_tien),
            "no_moi": float(no_moi)
        }

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
