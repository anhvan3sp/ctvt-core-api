from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from decimal import Decimal
from datetime import datetime, timedelta
from app.models import KhachHang, SanPham
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
    CongNoKhachHang,
    CongNoKhachHangLog
)

router = APIRouter(prefix="/sale", tags=["Sale"])


# =========================
# TIME VN
# =========================
def now_vn():
    return datetime.utcnow() + timedelta(hours=7)


def to_decimal(val):
    return Decimal(str(val or 0))


# =========================
# CREATE (NHÁP)
# =========================
@router.post("/")
def create_sale(
    data: HoaDonBanCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nhan_vien,nv_dac_biet"]))
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

        tien_mat = to_decimal(data.tien_mat)
        tien_ck = to_decimal(data.tien_ck)
        tong_thanh_toan = tien_mat + tien_ck
        no_lai = tong_tien - tong_thanh_toan

        # =========================
        # TẠO NHÁP
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
            trang_thai="nhap"   # 🔥 KHÁC DUY NHẤT
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
        return {"message": "Đã lưu nháp", "id": hoa_don.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


# =========================
# CONFIRM (THỰC SỰ GHI SỔ)
# =========================
@router.post("/confirm")
def confirm_sale(
    id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nhan_vien"]))
):
    try:
        now = now_vn()

        # 🔥 LOCK
        hoa_don = db.execute(
            select(HoaDonBan)
            .where(HoaDonBan.id == id)
            .with_for_update()
        ).scalar_one_or_none()

        if not hoa_don:
            raise HTTPException(404, "Không tìm thấy")

        if hoa_don.trang_thai == "xac_nhan":
            return {"msg": "ALREADY_CONFIRMED"}

        if hoa_don.trang_thai != "nhap":
            raise HTTPException(400, "Không hợp lệ")

        chi_tiets = db.query(HoaDonBanChiTiet)\
            .filter_by(id_hoa_don=id).all()

        # =========================
        # TRỪ KHO
        # =========================
        for item in chi_tiets:
            ton = db.query(TonKhoChotNgay)\
                .filter_by(ma_kho=hoa_don.ma_kho, ma_sp=item.ma_sp)\
                .with_for_update()\
                .first()

            if not ton or ton.so_luong < item.so_luong:
                raise HTTPException(400, "Không đủ hàng")

            ton.so_luong -= item.so_luong

            db.add(NhatKyKho(
                ma_kho=hoa_don.ma_kho,
                ma_sp=item.ma_sp,
                loai="xuat",
                so_luong=item.so_luong,
                ma_nv=user.ma_nv,
                ngay=now
            ))

        # =========================
        # QUỸ
        # =========================
        quy_ct = db.query(QuyCongTyChotNgay).with_for_update().first()
        quy_nv = db.query(QuyNhanVienChotNgay)\
            .filter_by(ma_nv=user.ma_nv)\
            .with_for_update().first()

        if hoa_don.tien_mat > 0:
            quy_nv.so_du += hoa_don.tien_mat

        if hoa_don.tien_ck > 0:
            quy_ct.tien_ngan_hang += hoa_don.tien_ck

        # =========================
        # CÔNG NỢ
        # =========================
        cn = db.query(CongNoKhachHang)\
            .filter_by(ma_kh=hoa_don.ma_kh)\
            .with_for_update().first()

        if not cn:
            cn = CongNoKhachHang(ma_kh=hoa_don.ma_kh, so_du=Decimal("0"))
            db.add(cn)
            db.flush()

        cn.so_du += hoa_don.no_lai

        db.add(CongNoKhachHangLog(
            ma_kh=hoa_don.ma_kh,
            ngay=now,
            phat_sinh=hoa_don.no_lai,
            loai="ban_hang"
        ))

        # =========================
        # UPDATE TRẠNG THÁI
        # =========================
        hoa_don.trang_thai = "xac_nhan"

        db.commit()

        return {"msg": "XAC_NHAN_OK"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


# =========================
# CANCEL
# =========================
@router.post("/cancel")
def cancel_sale(
    id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nhan_vien"]))
):
    try:
        hoa_don = db.execute(
            select(HoaDonBan)
            .where(HoaDonBan.id == id)
            .with_for_update()
        ).scalar_one_or_none()

        if not hoa_don:
            raise HTTPException(404, "Không tìm thấy")

        if hoa_don.trang_thai == "huy":
            return {"msg": "ALREADY_CANCELED"}

        if hoa_don.trang_thai != "nhap":
            raise HTTPException(400, "Chỉ huỷ khi đang nháp")

        hoa_don.trang_thai = "huy"

        db.commit()

        return {"msg": "HUY_OK"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))



# =========================
# GET TODAY (SALE )
# =========================

@router.get("/today")
def get_today_sale(
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nhan_vien"]))
):
    today = now_vn().date()

    sales = (
        db.query(HoaDonBan, KhachHang.ten_cua_hang)
        .outerjoin(KhachHang, HoaDonBan.ma_kh == KhachHang.ma_kh)
        .filter(
            HoaDonBan.ngay == today,
            HoaDonBan.ma_nv == user.ma_nv
        )
        .order_by(HoaDonBan.id.desc())
        .all()
    )

    result = []

    for s, ten_kh in sales:

        chi_tiet = (
            db.query(HoaDonBanChiTiet, SanPham.ten_sp)
            .join(SanPham, HoaDonBanChiTiet.ma_sp == SanPham.ma_sp)
            .filter(HoaDonBanChiTiet.id_hoa_don == s.id)
            .all()
        )

        items = []

        for ct, ten_sp in chi_tiet:
            items.append({
                "ten_sp": ten_sp,
                "so_luong": float(ct.so_luong),
                "don_gia": float(ct.don_gia),
                "thanh_tien": float(ct.thanh_tien)
            })

        result.append({
            "id": s.id,
            "ten_kh": ten_kh or "",
            "tong_tien": float(s.tong_thanh_toan or 0),
            "trang_thai": s.trang_thai,
            "items": items
        })

    return result
