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
    HoaDonNhapChiTiet,
    TonKhoChotNgay,
    NhatKyKho,
    QuyCongTyChotNgay,
    QuyNhanVienChotNgay,
    ThuChi,
    CongNoNCC,
    CongNoNCCLog
)

router = APIRouter(prefix="/purchase", tags=["Purchase"])


def to_decimal(val):
    try:
        return Decimal(str(val or 0))
    except:
        raise HTTPException(400, "Tiền không hợp lệ")


@router.post("/")
def create_purchase(
    data: HoaDonNhapCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nv_dac_biet"]))
):
    try:
        # 🔥 DÙNG DUY NHẤT 1 TIME
        now = datetime.now()

        # =========================
        # VALIDATE
        # =========================
        if not data.items:
            raise HTTPException(400, "Không có sản phẩm")

        tong_tien = Decimal("0")

        for item in data.items:
            if not item.ma_sp:
                raise HTTPException(400, "Thiếu sản phẩm")

            sl = Decimal(str(item.so_luong))
            gia = Decimal(str(item.don_gia))

            if sl <= 0:
                raise HTTPException(400, "Số lượng phải > 0")

            tong_tien += sl * gia

        # =========================
        # CHECK TRÙNG
        # =========================
        existing = db.execute(text("""
            SELECT id FROM hoa_don_nhap
            WHERE DATE(ngay) = :ngay
              AND ma_nv = :ma_nv
              AND ma_ncc = :ma_ncc
              AND tong_tien = :tong_tien
            LIMIT 1
        """), {
            "ngay": now.date(),
            "ma_nv": user.ma_nv,
            "ma_ncc": data.ma_ncc,
            "tong_tien": tong_tien
        }).fetchone()

        if existing and not getattr(data, "force", False):
            raise HTTPException(409, "HOA_DON_TRUNG")

        # =========================
        # LOCK QUỸ
        # =========================
        quy_ct = db.query(QuyCongTyChotNgay).with_for_update().first()

        if not quy_ct:
            raise HTTPException(400, "Thiếu quỹ công ty")

        quy_nv = None
        if user.vai_tro != "admin":
            quy_nv = db.query(QuyNhanVienChotNgay)\
                .filter_by(ma_nv=user.ma_nv)\
                .with_for_update()\
                .first()

            if not quy_nv:
                raise HTTPException(400, "Thiếu quỹ nhân viên")

        # =========================
        # TĂNG KHO
        # =========================
        for item in data.items:
            sl = Decimal(str(item.so_luong))

            ton = db.query(TonKhoChotNgay)\
                .filter_by(ma_kho=data.ma_kho, ma_sp=item.ma_sp)\
                .with_for_update()\
                .first()

            if not ton:
                ton = TonKhoChotNgay(
                    ma_kho=data.ma_kho,
                    ma_sp=item.ma_sp,
                    so_luong=Decimal("0")
                )
                db.add(ton)
                db.flush()

            ton.so_luong += sl

            db.add(NhatKyKho(
                ma_kho=data.ma_kho,
                ma_sp=item.ma_sp,
                loai="nhap",
                so_luong=sl,
                ma_nv=user.ma_nv,
                ngay=now
            ))

        # =========================
        # TIỀN
        # =========================
        tien_mat = to_decimal(data.tien_mat)
        tien_ck = to_decimal(data.tien_ck)

        tong_thanh_toan = tien_mat + tien_ck
        no_moi = tong_tien - tong_thanh_toan

        if user.vai_tro == "admin":
            if tien_mat > 0:
                quy_ct.tien_mat -= tien_mat
            if tien_ck > 0:
                quy_ct.tien_ngan_hang -= tien_ck
        else:
            if tien_mat > 0:
                quy_nv.so_du -= tien_mat
            if tien_ck > 0:
                quy_ct.tien_ngan_hang -= tien_ck

        # =========================
        # CÔNG NỢ NCC
        # =========================
        cn = db.query(CongNoNCC)\
            .filter_by(ma_ncc=data.ma_ncc)\
            .with_for_update()\
            .first()

        if not cn:
            cn = CongNoNCC(ma_ncc=data.ma_ncc, so_du=Decimal("0"))
            db.add(cn)
            db.flush()

        cn.so_du += no_moi

        db.add(CongNoNCCLog(
            ma_ncc=data.ma_ncc,
            ngay=now,
            phat_sinh=no_moi,
            loai="nhap_hang"
        ))

        # =========================
        # THU CHI
        # =========================
        if tien_mat > 0:
            db.add(ThuChi(
                ngay=now,
                doi_tuong="cong_ty" if user.vai_tro == "admin" else "nhan_vien",
                ma_nv=user.ma_nv,
                so_tien=tien_mat,
                loai="chi",
                hinh_thuc="tien_mat",
                loai_giao_dich="nhap_hang"
            ))

        if tien_ck > 0:
            db.add(ThuChi(
                ngay=now,
                doi_tuong="cong_ty",
                ma_nv=user.ma_nv,
                so_tien=tien_ck,
                loai="chi",
                hinh_thuc="chuyen_khoan",
                loai_giao_dich="nhap_hang"
            ))

        # =========================
        # HÓA ĐƠN (🔥 FIX CHÍNH)
        # =========================
        hoa_don = HoaDonNhap(
            ngay=now.date(),
            ngay_tao=now,   # 🔥 CHỐT LỖI TIME Ở ĐÂY
            ma_nv=user.ma_nv,
            ma_ncc=data.ma_ncc,
            ma_kho=data.ma_kho,
            tong_tien=tong_tien,
            tien_mat=tien_mat,
            tien_ck=tien_ck,
            tong_thanh_toan=tong_thanh_toan,
            trang_thai="xac_nhan"
        )

        db.add(hoa_don)
        db.flush()

        # =========================
        # CHI TIẾT
        # =========================
        chi_tiet_list = []

        for item in data.items:
            sl = Decimal(str(item.so_luong))
            gia = Decimal(str(item.don_gia))

            chi_tiet_list.append(HoaDonNhapChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=sl,
                don_gia=gia,
                thanh_tien=sl * gia
            ))

        db.add_all(chi_tiet_list)

        db.commit()

        return {"message": "OK"}

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
