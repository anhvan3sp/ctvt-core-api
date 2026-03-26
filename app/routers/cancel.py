from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.auth_utils import get_current_user
from app.models import (
    HoaDonBan,
    HoaDonBanChiTiet,
    HoaDonNhap,
    HoaDonNhapChiTiet,
    NhatKyKho,
    TonKhoChotNgay,
    ThuChi,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    CongNoKhachHang,
    CongNoKhachHangLog,
    CongNoNCC,
    CongNoNCCLog
)

router = APIRouter(prefix="/transaction", tags=["cancel"])


@router.post("/cancel")
def cancel_transaction(
    loai: str,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:

        if loai == "ban":

            hoa_don = db.query(HoaDonBan)\
                .filter_by(id=id)\
                .with_for_update()\
                .first()

            if not hoa_don:
                raise HTTPException(404, "Không tìm thấy")

            if hoa_don.trang_thai == "huy":
                raise HTTPException(400, "Đã huỷ rồi")

            # =====================
            # 1. HOÀN KHO
            # =====================
            chi_tiet = db.query(HoaDonBanChiTiet)\
                .filter_by(id_hoa_don=id).all()

            for ct in chi_tiet:

                ton = db.query(TonKhoChotNgay)\
                    .filter_by(ma_kho=hoa_don.ma_kho, ma_sp=ct.ma_sp)\
                    .with_for_update()\
                    .first()

                ton.so_luong += ct.so_luong

                db.add(NhatKyKho(
                    ma_kho=hoa_don.ma_kho,
                    ma_sp=ct.ma_sp,
                    loai="nhap",  # đảo
                    so_luong=ct.so_luong,
                    ma_nv=user.ma_nv,
                    ngay=datetime.now()
                ))

            # =====================
            # 2. ĐẢO TIỀN
            # =====================
            quy_nv = db.query(QuyNhanVienChotNgay)\
                .filter_by(ma_nv=hoa_don.ma_nv)\
                .with_for_update()\
                .first()

            quy_ct = db.query(QuyCongTyChotNgay)\
                .with_for_update()\
                .first()

            if hoa_don.tien_mat > 0:
                quy_nv.so_du -= hoa_don.tien_mat

                db.add(ThuChi(
                    ngay=datetime.now(),
                    doi_tuong="nhan_vien",
                    ma_nv=user.ma_nv,
                    so_tien=hoa_don.tien_mat,
                    loai="chi",  # đảo
                    hinh_thuc="tien_mat",
                    loai_giao_dich="huy_ban"
                ))

            if hoa_don.tien_ck > 0:
                quy_ct.tien_ngan_hang -= hoa_don.tien_ck

                db.add(ThuChi(
                    ngay=datetime.now(),
                    doi_tuong="cong_ty",
                    ma_nv=user.ma_nv,
                    so_tien=hoa_don.tien_ck,
                    loai="chi",
                    hinh_thuc="chuyen_khoan",
                    loai_giao_dich="huy_ban"
                ))

            # =====================
            # 3. ĐẢO CÔNG NỢ
            # =====================
            cn = db.query(CongNoKhachHang)\
                .filter_by(ma_kh=hoa_don.ma_kh)\
                .with_for_update()\
                .first()

            if cn:
                cn.so_du -= hoa_don.no_lai

                db.add(CongNoKhachHangLog(
                    ma_kh=hoa_don.ma_kh,
                    ngay=datetime.now(),
                    phat_sinh=-hoa_don.no_lai,
                    loai="huy_ban"
                ))

            # =====================
            # 4. ĐÁNH DẤU
            # =====================
            hoa_don.trang_thai = "huy"

        # =========================
        # NHẬP HÀNG (tương tự)
        # =========================
        elif loai == "nhap":

            hoa_don = db.query(HoaDonNhap)\
                .filter_by(id=id)\
                .with_for_update()\
                .first()

            if not hoa_don:
                raise HTTPException(404, "Không tìm thấy")

            if hoa_don.trang_thai == "huy":
                raise HTTPException(400, "Đã huỷ rồi")

            chi_tiet = db.query(HoaDonNhapChiTiet)\
                .filter_by(id_hoa_don=id).all()

            for ct in chi_tiet:

                ton = db.query(TonKhoChotNgay)\
                    .filter_by(ma_kho=hoa_don.ma_kho, ma_sp=ct.ma_sp)\
                    .with_for_update()\
                    .first()

                ton.so_luong -= ct.so_luong

                db.add(NhatKyKho(
                    ma_kho=hoa_don.ma_kho,
                    ma_sp=ct.ma_sp,
                    loai="xuat",
                    so_luong=ct.so_luong,
                    ma_nv=user.ma_nv,
                    ngay=datetime.now()
                ))

            hoa_don.trang_thai = "huy"

        else:
            raise HTTPException(400, "Loại không hợp lệ")

        db.commit()
        return {"msg": "Đã huỷ thành công"}

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
