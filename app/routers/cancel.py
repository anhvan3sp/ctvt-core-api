from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date

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
    KhachHang,
    SanPham
)

router = APIRouter(prefix="/transaction", tags=["cancel"])


# =====================================================
# 🔥 API: LẤY DANH SÁCH GIAO DỊCH TRONG NGÀY
# =====================================================

@router.get("/today")
def get_today_transactions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    today = date.today()

    result = []

    # =========================
    # BÁN HÀNG
    # =========================
    sales = (
        db.query(HoaDonBan, KhachHang.ten_cua_hang)
        .outerjoin(KhachHang, HoaDonBan.ma_kh == KhachHang.ma_kh)
        .filter(
            HoaDonBan.ngay == today,
            HoaDonBan.ma_nv == user.ma_nv
        )
        .all()
    )

    for s, ten_kh in sales:

        chi_tiet = (
            db.query(HoaDonBanChiTiet, SanPham.ten_sp)
            .join(SanPham, HoaDonBanChiTiet.ma_sp == SanPham.ma_sp)
            .filter(HoaDonBanChiTiet.id_hoa_don == s.id)
            .all()
        )

        chi_tiet_list = []

        for ct, ten_sp in chi_tiet:
            chi_tiet_list.append({
                "ten_hang": ten_sp,
                "so_luong": float(ct.so_luong),
                "don_gia": float(ct.don_gia),
                "thanh_tien": float(ct.thanh_tien)
            })

        result.append({
            "id": s.id,
            "loai": "ban",
            "ten_kh": ten_kh or "",
            "chi_tiet": chi_tiet_list,
            "tong_tien": float(s.tong_thanh_toan or 0),
            "trang_thai": s.trang_thai
        })

    # =========================
    # NHẬP HÀNG
    # =========================
    purchases = (
        db.query(HoaDonNhap)
        .filter(
            HoaDonNhap.ngay == today,
            HoaDonNhap.ma_nv == user.ma_nv
        )
        .all()
    )

    for p in purchases:

        chi_tiet = (
            db.query(HoaDonNhapChiTiet, SanPham.ten_sp)
            .join(SanPham, HoaDonNhapChiTiet.ma_sp == SanPham.ma_sp)
            .filter(HoaDonNhapChiTiet.id_hoa_don == p.id)
            .all()
        )

        chi_tiet_list = []

        for ct, ten_sp in chi_tiet:
            chi_tiet_list.append({
                "ten_hang": ten_sp,
                "so_luong": float(ct.so_luong),
                "don_gia": float(ct.don_gia),
                "thanh_tien": float(ct.thanh_tien)
            })

        result.append({
            "id": p.id,
            "loai": "nhap",
            "ten_kh": "Nhà cung cấp",
            "chi_tiet": chi_tiet_list,
            "tong_tien": float(p.tong_tien or 0),
            "trang_thai": p.trang_thai
        })

    # =========================
    # THU CHI
    # =========================
    thu_chi = (
        db.query(ThuChi)
        .filter(
            func.date(ThuChi.ngay) == today,
            ThuChi.ma_nv == user.ma_nv
        )
        .all()
    )

    for t in thu_chi:
        result.append({
            "id": t.id,
            "loai": "thu_chi",
            "ten_kh": t.noi_dung or "Thu/Chi",
            "chi_tiet": [
                {
                    "ten_hang": t.loai_giao_dich or "khac",
                    "so_luong": 1,
                    "don_gia": float(t.so_tien),
                    "thanh_tien": float(t.so_tien)
                }
            ],
            "tong_tien": float(t.so_tien),
            "trang_thai": "huy" if t.is_reversal else "active"
        })

    return result


# =====================================================
# 🔥 API: HUỶ GIAO DỊCH
# =====================================================

@router.post("/cancel")
def cancel_transaction(
    loai: str,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:

        # =========================
        # BÁN HÀNG
        # =========================
        if loai == "ban":

            hoa_don = db.query(HoaDonBan)\
                .filter_by(id=id)\
                .with_for_update()\
                .first()

            if not hoa_don:
                raise HTTPException(404, "Không tìm thấy")

            if hoa_don.trang_thai == "huy":
                raise HTTPException(400, "Đã huỷ rồi")

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
                    loai="nhap",
                    so_luong=ct.so_luong,
                    ma_nv=user.ma_nv,
                    ngay=datetime.now()
                ))

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
                    loai="chi",
                    hinh_thuc="tien_mat",
                    loai_giao_dich="ban_hang",  # ✅ FIX
                    noi_dung="HUỶ HOÁ ĐƠN BÁN",
                    is_reversal=1,
                    ref_id=hoa_don.id,
                    created_by=user.ma_nv
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
                    loai_giao_dich="ban_hang",  # ✅ FIX
                    noi_dung="HUỶ HOÁ ĐƠN BÁN",
                    is_reversal=1,
                    ref_id=hoa_don.id,
                    created_by=user.ma_nv
                ))

            hoa_don.trang_thai = "huy"

        # =========================
        # NHẬP HÀNG
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

        # =========================
        # THU CHI
        # =========================
        elif loai == "thu_chi":

            record = db.query(ThuChi)\
                .filter_by(id=id)\
                .with_for_update()\
                .first()

            if not record:
                raise HTTPException(404, "Không tìm thấy")

            existed = db.query(ThuChi).filter(
                ThuChi.ref_id == record.id,
                ThuChi.is_reversal == 1
            ).first()

            if existed:
                raise HTTPException(400, "Đã huỷ trước đó")

            quy_ct = db.query(QuyCongTyChotNgay)\
                .with_for_update()\
                .first()

            quy_nv = db.query(QuyNhanVienChotNgay)\
                .filter_by(ma_nv=record.ma_nv)\
                .with_for_update()\
                .first()

            so_tien = record.so_tien

            if record.loai == "chi":
                quy_nv.so_du += so_tien if record.hinh_thuc == "tien_mat" else 0
                quy_ct.tien_ngan_hang += so_tien if record.hinh_thuc != "tien_mat" else 0
                loai_moi = "thu"
            else:
                quy_nv.so_du -= so_tien if record.hinh_thuc == "tien_mat" else 0
                quy_ct.tien_ngan_hang -= so_tien if record.hinh_thuc != "tien_mat" else 0
                loai_moi = "chi"

            db.add(ThuChi(
                ngay=datetime.now(),
                doi_tuong=record.doi_tuong,
                ma_nv=record.ma_nv,
                so_tien=so_tien,
                loai=loai_moi,
                hinh_thuc=record.hinh_thuc,
                loai_giao_dich=record.loai_giao_dich,  # ✅ FIX
                noi_dung="HUỶ: " + (record.noi_dung or ""),
                is_reversal=1,
                ref_id=record.id,
                created_by=user.ma_nv
            ))

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
