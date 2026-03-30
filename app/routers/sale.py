from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas import HoaDonBanCreate
from app.auth_utils import require_roles
from app.models import (
    HoaDonBan,
    HoaDonBanChiTiet,
    TonKhoChotNgay,
    NhatKyKho,
    QuyCongTyChotNgay,
    QuyNhanVienChotNgay,
    ThuChi,
    CongNoKhachHang,
    CongNoKhachHangLog
)

router = APIRouter(prefix="/sale", tags=["Sale"])


def now_vn():
    return datetime.utcnow() + timedelta(hours=7)


def to_decimal(val):
    return Decimal(str(val or 0))


@router.post("/")
def create_sale(
    data: HoaDonBanCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nhan_vien"]))
):
    try:
        now = now_vn()

        if not data.items:
            raise HTTPException(400, "Không có sản phẩm")

        tong_tien = Decimal("0")

        for item in data.items:
            sl = to_decimal(item.so_luong)
            gia = to_decimal(item.don_gia)

            if sl <= 0:
                raise HTTPException(400, "Số lượng phải > 0")

            tong_tien += sl * gia

        # =========================
        # TRỪ KHO
        # =========================
        for item in data.items:
            sl = to_decimal(item.so_luong)

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
                ngay=now
            ))

        tien_mat = to_decimal(data.tien_mat)
        tien_ck = to_decimal(data.tien_ck)

        tong_thanh_toan = tien_mat + tien_ck
        no_lai = tong_tien - tong_thanh_toan

        # =========================
        # QUỸ
        # =========================
        quy_ct = db.query(QuyCongTyChotNgay).with_for_update().first()
        quy_nv = db.query(QuyNhanVienChotNgay)\
            .filter_by(ma_nv=user.ma_nv)\
            .with_for_update().first()

        if tien_mat > 0:
            quy_nv.so_du += tien_mat

        if tien_ck > 0:
            quy_ct.tien_ngan_hang += tien_ck

        # =========================
        # CÔNG NỢ KH
        # =========================
        cn = db.query(CongNoKhachHang)\
            .filter_by(ma_kh=data.ma_kh)\
            .with_for_update().first()

        if not cn:
            cn = CongNoKhachHang(ma_kh=data.ma_kh, so_du=Decimal("0"))
            db.add(cn)
            db.flush()

        cn.so_du += no_lai

        db.add(CongNoKhachHangLog(
            ma_kh=data.ma_kh,
            ngay=now,
            phat_sinh=no_lai,
            loai="ban_hang"
        ))

        # =========================
        # HÓA ĐƠN
        # =========================
        hoa_don = HoaDonBan(
            ngay=now.date(),
            ngay_tao=now,
            ma_kh=data.ma_kh,
            ma_nv=user.ma_nv,
            ma_kho=data.ma_kho,
            tong_tien=tong_tien,
            tien_mat=tien_mat,
            tien_ck=tien_ck,
            tong_thanh_toan=tong_thanh_toan,
            no_lai=no_lai,
            trang_thai="xac_nhan"
        )

        db.add(hoa_don)
        db.flush()

        # =========================
        # CHI TIẾT
        # =========================
        chi_tiet = []
        for item in data.items:
            sl = to_decimal(item.so_luong)
            gia = to_decimal(item.don_gia)

            chi_tiet.append(HoaDonBanChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=sl,
                don_gia=gia,
                thanh_tien=sl * gia
            ))

        db.add_all(chi_tiet)

        db.commit()
        return {"message": "OK"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
