from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal
from datetime import datetime

from app.database import get_db
from app.schemas import HoaDonBanCreate
from app.auth_utils import require_roles
from app.models import (
    HoaDonBan,
    TonKhoChotNgay,
    NhatKyKho,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    ThuChi,
    KhachHang
)

router = APIRouter(prefix="/sale", tags=["Sale"])


def to_decimal(val):
    try:
        return Decimal(str(val or 0))
    except:
        raise HTTPException(400, "Tiền không hợp lệ")


@router.post("/")
def create_sale(
    data: HoaDonBanCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nv_dac_biet"]))
):

    try:

        # =========================
        # CHECK QUYỀN KHO
        # =========================
        if user.vai_tro != "admin":
            row = db.execute(text("""
                SELECT 1 FROM nhan_vien_kho
                WHERE ma_nv = :ma_nv AND ma_kho = :ma_kho
            """), {
                "ma_nv": user.ma_nv,
                "ma_kho": data.ma_kho
            }).fetchone()

            if not row:
                raise HTTPException(403, "Không được phép dùng kho")

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

        # =========================
        # LOCK KHÁCH
        # =========================
        kh = db.query(KhachHang)\
            .filter_by(ma_kh=data.ma_kh)\
            .with_for_update()\
            .first()

        if not quy_nv or not quy_ct or not kh:
            raise HTTPException(400, "Thiếu dữ liệu")

        tong_tien = Decimal("0")

        # =========================
        # XỬ LÝ KHO
        # =========================
        for item in data.items:

            ton = db.query(TonKhoChotNgay)\
                .filter_by(ma_kho=data.ma_kho, ma_sp=item.ma_sp)\
                .with_for_update()\
                .first()

            if not ton or ton.so_luong < item.so_luong:
                raise HTTPException(400, "Không đủ hàng")

            ton.so_luong -= item.so_luong

            db.add(NhatKyKho(
                ma_kho=data.ma_kho,
                ma_sp=item.ma_sp,
                loai="xuat",
                so_luong=item.so_luong,
                ma_nv=user.ma_nv,
                ngay=datetime.now()
            ))

            tong_tien += Decimal(item.so_luong) * Decimal(item.don_gia)

        tien_mat = to_decimal(data.tien_mat)
        tien_ck = to_decimal(data.tien_ck)

        if tien_mat + tien_ck > tong_tien:
            raise HTTPException(400, "Tiền lớn hơn tổng tiền")

        # =========================
        # TIỀN
        # =========================
        quy_nv.so_du = (quy_nv.so_du or 0) + tien_mat
        quy_ct.tien_ngan_hang = (quy_ct.tien_ngan_hang or 0) + tien_ck

        # =========================
        # CÔNG NỢ
        # =========================
        no_moi = tong_tien - tien_mat - tien_ck

        if no_moi > 0:
            kh.cong_no = (kh.cong_no or 0) + no_moi

        # =========================
        # UPDATE QUỸ
        # =========================
        quy_ct.tong_quy = (quy_ct.tien_mat or 0) + (quy_ct.tien_ngan_hang or 0)

        # =========================
        # LOG TIỀN (FIX CHUẨN)
        # =========================
        if tien_mat > 0:
            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong="nhan_vien",   # 🔥 BẮT BUỘC
                ma_nv=user.ma_nv,
                so_tien=tien_mat,
                loai="thu",
                hinh_thuc="tien_mat",
                loai_giao_dich="ban_hang",
                so_du_sau=quy_nv.so_du,
                so_du_ct_sau=quy_ct.tong_quy
            ))

        if tien_ck > 0:
            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong="cong_ty",   # 🔥 BẮT BUỘC
                ma_nv=user.ma_nv,
                so_tien=tien_ck,
                loai="thu",
                hinh_thuc="chuyen_khoan",
                loai_giao_dich="ban_hang",
                so_du_sau=quy_nv.so_du,
                so_du_ct_sau=quy_ct.tong_quy
            ))

        # =========================
        # TẠO HÓA ĐƠN
        # =========================
        db.add(HoaDonBan(
            ngay=datetime.now(),
            ma_nv=user.ma_nv,
            ma_kh=data.ma_kh,
            ma_kho=data.ma_kho,
            tong_tien=tong_tien,
            tien_mat=tien_mat,
            tien_ck=tien_ck,
            tong_thanh_toan=tien_mat + tien_ck,
            no_lai=no_moi
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
