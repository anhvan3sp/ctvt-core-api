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
    KhachHang,
    CongNoKhachHang
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

        if not quy_nv or not quy_ct:
            raise HTTPException(400, "Thiếu quỹ")

        # =========================
        # LOCK KHÁCH
        # =========================
        kh = db.query(KhachHang)\
            .filter_by(ma_kh=data.ma_kh)\
            .with_for_update()\
            .first()

        if not kh:
            raise HTTPException(400, "Không có khách")

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

            if not ton or ton.so_luong < sl:
                raise HTTPException(400, "Không đủ hàng")

            ton.so_luong -= sl

            db.add(NhatKyKho(
                ma_kho=data.ma_kho,
                ma_sp=item.ma_sp,
                loai="xuat",
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

        # =========================
        # UPDATE QUỸ
        # =========================
        if tien_mat > 0:
            quy_nv.so_du += tien_mat

        if tien_ck > 0:
            quy_ct.tien_ngan_hang += tien_ck

        # =========================
        # CÔNG NỢ (AUTO CREATE + SAFE)
        # =========================
        no_moi = tong_tien - tong_thanh_toan

        cn = db.query(CongNoKhachHang)\
            .filter_by(ma_kh=data.ma_kh)\
            .with_for_update()\
            .first()

        if not cn:
            cn = CongNoKhachHang(
                ma_kh=data.ma_kh,
                so_du=Decimal("0")
            )
            db.add(cn)
            db.flush()  # 🔥 đảm bảo insert ngay trong transaction

        # 🔥 1 dòng xử lý tất cả case (thiếu / đủ / dư)
        cn.so_du += no_moi

        # =========================
        # LOG THU CHI
        # =========================
        if tien_mat > 0:
            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong="nhan_vien",
                ma_nv=user.ma_nv,
                so_tien=tien_mat,
                loai="thu",
                hinh_thuc="tien_mat",
                loai_giao_dich="ban_hang",
                so_du_sau=quy_nv.so_du,
                ma_kh=data.ma_kh
            ))

        if tien_ck > 0:
            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong="cong_ty",
                ma_nv=user.ma_nv,
                so_tien=tien_ck,
                loai="thu",
                hinh_thuc="chuyen_khoan",
                loai_giao_dich="ban_hang",
                so_du_ct_sau=quy_ct.tien_ngan_hang,
                ma_kh=data.ma_kh
            ))

        # =========================
        # HÓA ĐƠN
        # =========================
        hoa_don = HoaDonBan(
            ngay=datetime.now(),
            ma_nv=user.ma_nv,
            ma_kh=data.ma_kh,
            ma_kho=data.ma_kho,
            tong_tien=tong_tien,
            tien_mat=tien_mat,
            tien_ck=tien_ck,
            tong_thanh_toan=tong_thanh_toan,
            no_lai=no_moi
        )

        db.add(hoa_don)

        # =========================
        # COMMIT
        # =========================
        db.commit()

        return {
            "message": "OK",
            "tong_tien": float(tong_tien),
            "da_tra": float(tong_thanh_toan),
            "no_lai": float(no_moi),
            "cong_no_sau": float(cn.so_du)
        }

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
