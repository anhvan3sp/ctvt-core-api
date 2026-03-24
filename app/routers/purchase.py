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

        # =========================
        # LOCK DỮ LIỆU
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

        # =========================
        # TÍNH TIỀN + KHO
        # =========================
        tong_tien = Decimal("0")

        for item in data.items:

            sl = Decimal(str(item.so_luong))
            gia = Decimal(str(item.don_gia))

            ton = db.query(TonKhoChotNgay)\
                .filter_by(ma_kho=data.ma_kho, ma_sp=item.ma_sp)\
                .with_for_update()\
                .first()

            if not ton:
                raise HTTPException(400, "Chưa có tồn kho")

            ton.so_luong += sl

            db.add(NhatKyKho(
                ma_kho=data.ma_kho,
                ma_sp=item.ma_sp,
                loai="nhap",
                so_luong=sl,
                ma_nv=user.ma_nv,
                ngay=datetime.now()
            ))

            tong_tien += sl * gia

        # =========================
        # TIỀN
        # =========================
        tien_mat = to_decimal(data.tien_mat)
        tien_ck = to_decimal(data.tien_ck)

        tong_thanh_toan = tien_mat + tien_ck

        # ❌ chỉ chặn trả dư
        if tong_thanh_toan > tong_tien:
            raise HTTPException(400, "Tiền vượt tổng")

        # =========================
        # XỬ LÝ QUỸ
        # =========================

        # ===== ADMIN =====
        if user.ma_nv == "admin":

            if tien_mat > 0:
                if quy_ct.tien_mat < tien_mat:
                    raise HTTPException(400, "Thiếu tiền mặt")
                quy_ct.tien_mat -= tien_mat

            if tien_ck > 0:
                if quy_ct.tien_ngan_hang < tien_ck:
                    raise HTTPException(400, "Thiếu CK")
                quy_ct.tien_ngan_hang -= tien_ck

        # ===== NHÂN VIÊN =====
        else:

            # 🔥 AUTO CREATE QUỸ NV
            if not quy_nv:
                quy_nv = QuyNhanVienChotNgay(
                    ma_nv=user.ma_nv,
                    so_du=Decimal("0")
                )
                db.add(quy_nv)
                db.flush()

            # tiền mặt → NV
            if tien_mat > 0:
                if quy_nv.so_du < tien_mat:
                    raise HTTPException(400, "Không đủ tiền mặt NV")
                quy_nv.so_du -= tien_mat

            # chuyển khoản → công ty
            if tien_ck > 0:
                if quy_ct.tien_ngan_hang < tien_ck:
                    raise HTTPException(400, "Thiếu tiền công ty")
                quy_ct.tien_ngan_hang -= tien_ck

        # =========================
        # CÔNG NỢ NCC
        # =========================
        no_moi = tong_tien - tong_thanh_toan

        if no_moi > 0:
            ncc.cong_no = (ncc.cong_no or Decimal("0")) + no_moi

        # =========================
        # UPDATE TỔNG QUỸ
        # =========================
        quy_ct.tong_quy = (quy_ct.tien_mat or 0) + (quy_ct.tien_ngan_hang or 0)

        # =========================
        # LOG THU CHI
        # =========================

        # tiền mặt
        if tien_mat > 0:
            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong="nhan_vien" if user.ma_nv != "admin" else "cong_ty",
                ma_nv=user.ma_nv,
                so_tien=tien_mat,
                loai="chi",
                hinh_thuc="tien_mat",
                loai_giao_dich="tra_no_ncc",
                so_du_sau=quy_nv.so_du if user.ma_nv != "admin" else None,
                so_du_ct_sau=quy_ct.tong_quy
            ))

        # chuyển khoản
        if tien_ck > 0:
            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong="cong_ty",
                ma_nv=user.ma_nv,
                so_tien=tien_ck,
                loai="chi",
                hinh_thuc="chuyen_khoan",
                loai_giao_dich="tra_no_ncc",
                so_du_ct_sau=quy_ct.tong_quy
            ))

        # =========================
        # HÓA ĐƠN
        # =========================
        db.add(HoaDonNhap(
            ngay=datetime.now(),
            ma_nv=user.ma_nv,
            ma_ncc=data.ma_ncc,
            ma_kho=data.ma_kho,
            tong_tien=tong_tien
        ))

        # =========================
        # COMMIT
        # =========================
        db.commit()

        return {
            "message": "OK",
            "tong_tien": float(tong_tien),
            "da_tra": float(tong_thanh_toan),
            "no_moi": float(no_moi)
        }

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
