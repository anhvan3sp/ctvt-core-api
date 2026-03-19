from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text

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


@router.post("/")
def create_purchase(
    data: HoaDonNhapCreate,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "nv_dac_biet"]))
):

    with db.begin():

        # =========================
        # LOCK QUỸ
        # =========================
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

        tong_tien = 0

        # =========================
        # XỬ LÝ KHO
        # =========================
        for item in data.items:

            ton = db.query(TonKhoChotNgay)\
                .filter_by(ma_kho=data.ma_kho, ma_sp=item.ma_sp)\
                .with_for_update()\
                .first()

            if not ton:
                raise HTTPException(400, f"Chưa có tồn kho {item.ma_sp}")

            ton.so_luong += item.so_luong

            db.add(NhatKyKho(
                ma_kho=data.ma_kho,
                ma_sp=item.ma_sp,
                loai="nhap",
                so_luong=item.so_luong,
                ma_nv=user.ma_nv
            ))

            tong_tien += item.so_luong * item.don_gia

        tien_mat = data.tien_mat or 0
        tien_ck = data.tien_ck or 0

        if tien_mat + tien_ck > tong_tien:
            raise HTTPException(400, "Tiền lớn hơn tổng")

        no_moi = tong_tien - tien_mat - tien_ck

        # =========================
        # CASE: ADMIN
        # =========================
        if user.ma_nv == "admin":

            if tien_mat > 0:
                if quy_ct.tien_mat < tien_mat:
                    raise HTTPException(400, "Không đủ tiền mặt")
                quy_ct.tien_mat -= tien_mat

            if tien_ck > 0:
                if quy_ct.tien_ngan_hang < tien_ck:
                    raise HTTPException(400, "Không đủ tiền CK")
                quy_ct.tien_ngan_hang -= tien_ck

        # =========================
        # CASE: NHÂN VIÊN
        # =========================
        else:

            if not quy_nv:
                raise HTTPException(400, "Chưa có quỹ NV")

            if tien_mat + tien_ck > quy_nv.so_du:
                raise HTTPException(400, "Không đủ tiền NV")

            quy_nv.so_du -= (tien_mat + tien_ck)

        # =========================
        # CÔNG NỢ NCC
        # =========================
        if no_moi > 0:
            ncc.cong_no = (ncc.cong_no or 0) + no_moi

        # =========================
        # UPDATE TỔNG QUỸ
        # =========================
        quy_ct.tong_quy = quy_ct.tien_mat + quy_ct.tien_ngan_hang

        # =========================
        # LOG TIỀN
        # =========================
        db.add(ThuChi(
            ma_nv=user.ma_nv,
            loai="chi",
            loai_giao_dich="nhap_hang",
            so_tien=tong_tien,
            hinh_thuc="tong_hop",
            so_du_sau=quy_nv.so_du if quy_nv else 0,
            so_du_ct_sau=quy_ct.tong_quy
        ))

        # =========================
        # HÓA ĐƠN
        # =========================
        db.add(HoaDonNhap(
            ma_nv=user.ma_nv,
            ma_ncc=data.ma_ncc,
            ma_kho=data.ma_kho,
            tong_tien=tong_tien
        ))

    return {
        "message": "Nhập hàng OK",
        "tong_tien": tong_tien,
        "no_moi": no_moi
    }
