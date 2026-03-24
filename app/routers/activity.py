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
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    ThuChi,
    CongNoKhachHang,
    CongNoKhachHangLog,
    NhaCungCap
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

    # ===== SALE =====
    sale = db.execute(text("""
        SELECT id, 'sale' as type, tong_tien, ngay
        FROM hoa_don_ban
        WHERE ma_nv = :ma_nv
        AND DATE(ngay) = CURDATE()
    """), {"ma_nv": user.ma_nv}).fetchall()

    # ===== PURCHASE =====
    purchase = db.execute(text("""
        SELECT id, 'purchase' as type, tong_tien, ngay
        FROM hoa_don_nhap
        WHERE ma_nv = :ma_nv
        AND DATE(ngay) = CURDATE()
    """), {"ma_nv": user.ma_nv}).fetchall()

    return [dict(r._mapping) for r in (sale + purchase)]


# =========================
# HUỶ SALE
# =========================
@router.post("/cancel/sale/{id}")
def cancel_sale(
    id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nv_dac_biet"]))
):

    try:
        hd = db.query(HoaDonBan)\
            .filter_by(id=id)\
            .with_for_update()\
            .first()

        if not hd:
            raise HTTPException(404, "Không tìm thấy")

        if hd.ma_nv != user.ma_nv and user.ma_nv != "admin":
            raise HTTPException(403, "Không có quyền")

        # ===== ĐẢO TIỀN =====
        quy_nv = db.query(QuyNhanVienChotNgay)\
            .filter_by(ma_nv=hd.ma_nv)\
            .first()

        quy_ct = db.query(QuyCongTyChotNgay).first()

        if hd.tien_mat:
            quy_nv.so_du -= hd.tien_mat

        if hd.tien_ck:
            quy_ct.tien_ngan_hang -= hd.tien_ck

        # ===== CÔNG NỢ =====
        cn = db.query(CongNoKhachHang)\
            .filter_by(ma_kh=hd.ma_kh)\
            .first()

        if cn:
            cn.so_du -= hd.no_lai

        db.add(CongNoKhachHangLog(
            ma_kh=hd.ma_kh,
            ngay=datetime.now(),
            phat_sinh=-hd.no_lai,
            loai=f"huy_hd_{id}"
        ))

        # ===== LOG =====
        db.add(ThuChi(
            ngay=datetime.now(),
            doi_tuong="cong_ty",
            ma_nv=user.ma_nv,
            so_tien=hd.tong_tien,
            loai="chi",
            hinh_thuc="tien_mat",
            loai_giao_dich=f"huy_hd_sale_{id}"
        ))

        db.commit()

        return {"message": "Đã huỷ sale"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


# =========================
# HUỶ PURCHASE
# =========================
@router.post("/cancel/purchase/{id}")
def cancel_purchase(
    id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nv_dac_biet"]))
):

    try:
        hd = db.query(HoaDonNhap)\
            .filter_by(id=id)\
            .with_for_update()\
            .first()

        if not hd:
            raise HTTPException(404, "Không tìm thấy")

        if hd.ma_nv != user.ma_nv and user.ma_nv != "admin":
            raise HTTPException(403, "Không có quyền")

        # ===== ĐẢO TIỀN =====
        quy_ct = db.query(QuyCongTyChotNgay).first()

        if hd.tien_mat:
            quy_ct.tien_mat += hd.tien_mat

        if hd.tien_ck:
            quy_ct.tien_ngan_hang += hd.tien_ck

        # ===== CÔNG NỢ NCC =====
        if hd.tong_tien > (hd.tien_mat + hd.tien_ck):
            no = hd.tong_tien - (hd.tien_mat + hd.tien_ck)

            ncc = db.query(NhaCungCap)\
                .filter_by(ma_ncc=hd.ma_ncc)\
                .first()

            if ncc:
                ncc.cong_no -= no

        # ===== LOG =====
        db.add(ThuChi(
            ngay=datetime.now(),
            doi_tuong="cong_ty",
            ma_nv=user.ma_nv,
            so_tien=hd.tong_tien,
            loai="thu",
            hinh_thuc="tien_mat",
            loai_giao_dich=f"huy_hd_purchase_{id}"
        ))

        db.commit()

        return {"message": "Đã huỷ purchase"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
