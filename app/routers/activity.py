from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.database import get_db
from app.auth_utils import require_roles
from app.models import (
    HoaDonBan,
    HoaDonNhap,
    TonKhoChotNgay,
    NhatKyKho,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    ThuChi,
    CongNoKhachHang,
    CongNoKhachHangLog,
    NhaCungCap,
    HoaDonBanChiTiet
)

router = APIRouter(prefix="/activity", tags=["Activity"])


# =========================
# LIST ALL TRONG NGÀY
# =========================
@router.get("/today")
def list_today(
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nv_dac_biet"]))
):

    sale = db.execute(text("""
        SELECT id, 'sale' as type, tong_tien, ngay, trang_thai
        FROM hoa_don_ban
        WHERE ma_nv = :ma_nv
        AND DATE(ngay) = CURDATE()
    """), {"ma_nv": user.ma_nv}).fetchall()

    purchase = db.execute(text("""
        SELECT id, 'purchase' as type, tong_tien, ngay, trang_thai
        FROM hoa_don_nhap
        WHERE ma_nv = :ma_nv
        AND DATE(ngay) = CURDATE()
    """), {"ma_nv": user.ma_nv}).fetchall()

    return [dict(r._mapping) for r in (sale + purchase)]


# =========================
# HUỶ SALE (CHUẨN)
# =========================
@router.post("/cancel/sale/{id}")
def cancel_sale(
    id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nv_dac_biet"]))
):
    try:

        # ===== LOCK HÓA ĐƠN =====
        hd = db.query(HoaDonBan)\
            .filter_by(id=id)\
            .with_for_update()\
            .first()

        if not hd:
            raise HTTPException(404, "Không tìm thấy")

        if hd.ma_nv != user.ma_nv and user.ma_nv != "admin":
            raise HTTPException(403, "Không có quyền")

        # ===== CHECK ĐÃ HUỶ =====
        if hd.trang_thai == "huy":
            raise HTTPException(400, "Hoá đơn đã huỷ")

        # =========================
        # 1. ĐẢO KHO (🔥 QUAN TRỌNG)
        # =========================
        items = db.query(HoaDonBanChiTiet)\
            .filter_by(id_hoa_don=hd.id)\
            .all()

        for item in items:
            ton = db.query(TonKhoChotNgay)\
                .filter_by(ma_kho=hd.ma_kho, ma_sp=item.ma_sp)\
                .with_for_update()\
                .first()

            ton.so_luong += item.so_luong

            db.add(NhatKyKho(
                ma_kho=hd.ma_kho,
                ma_sp=item.ma_sp,
                loai="nhap",
                so_luong=item.so_luong,
                ma_nv=user.ma_nv,
                ngay=datetime.now(),
                bang_tham_chieu="huy_sale",
                id_tham_chieu=hd.id
            ))

        # =========================
        # 2. ĐẢO TIỀN
        # =========================
        quy_nv = db.query(QuyNhanVienChotNgay)\
            .filter_by(ma_nv=hd.ma_nv)\
            .with_for_update()\
            .first()

        quy_ct = db.query(QuyCongTyChotNgay)\
            .with_for_update()\
            .first()

        if hd.tien_mat:
            quy_nv.so_du -= hd.tien_mat

        if hd.tien_ck:
            quy_ct.tien_ngan_hang -= hd.tien_ck

        # =========================
        # 3. ĐẢO CÔNG NỢ
        # =========================
        cn = db.query(CongNoKhachHang)\
            .filter_by(ma_kh=hd.ma_kh)\
            .with_for_update()\
            .first()

        if cn:
            cn.so_du -= hd.no_lai

        db.add(CongNoKhachHangLog(
            ma_kh=hd.ma_kh,
            ngay=datetime.now(),
            phat_sinh=-hd.no_lai,
            loai="huy_ban_hang",
            ref_id=hd.id
        ))

        # =========================
        # 4. LOG THU CHI
        # =========================
        if hd.tien_mat:
            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong="nhan_vien",
                ma_nv=hd.ma_nv,
                so_tien=hd.tien_mat,
                loai="chi",
                hinh_thuc="tien_mat",
                loai_giao_dich="huy_ban_hang"
            ))

        if hd.tien_ck:
            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong="cong_ty",
                ma_nv=hd.ma_nv,
                so_tien=hd.tien_ck,
                loai="chi",
                hinh_thuc="chuyen_khoan",
                loai_giao_dich="huy_ban_hang"
            ))

        # =========================
        # 5. UPDATE STATUS
        # =========================
        hd.trang_thai = "huy"

        db.commit()

        return {"message": "Đã huỷ sale"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
