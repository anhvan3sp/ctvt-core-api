from sqlalchemy.orm import Session
from sqlalchemy import func, text
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException

from app.models import (
    HoaDonNhap,
    HoaDonNhapChiTiet,
    HoaDonBan,
    HoaDonBanChiTiet,
    NhatKyKho,
    ThuChi,
    NhanVien,
    KhachHang,
    SanPham
)

from app.schemas import HoaDonNhapCreate, HoaDonBanCreate


# =====================================================
# CHI TIẾT HÓA ĐƠN BÁN
# =====================================================
def get_sale_detail(db: Session, hoa_don_id: int):

    hd = db.query(HoaDonBan).filter(HoaDonBan.id == hoa_don_id).first()
    if not hd:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")

    chi_tiet = db.query(HoaDonBanChiTiet).filter(
        HoaDonBanChiTiet.id_hoa_don == hoa_don_id
    ).all()

    items = []

    for ct in chi_tiet:

        sp = db.query(SanPham).filter(
            SanPham.ma_sp == ct.ma_sp
        ).first()

        items.append({
            "ma_sp": ct.ma_sp,
            "ten_sp": sp.ten_sp if sp else "",
            "so_luong": float(ct.so_luong),
            "don_gia": float(ct.don_gia),
            "thanh_tien": float(ct.thanh_tien)
        })

    return {
        "so_hd": hd.so_hd if hd.so_hd else str(hd.id),
        "ngay": hd.ngay,
        "items": items
    }


# =====================================================
# CHI TIẾT CÔNG NỢ KHÁCH
# =====================================================
def get_debt_detail(db: Session, ma_kh: str):

    hoa_dons = (
        db.query(HoaDonBan)
        .filter(HoaDonBan.ma_kh == ma_kh)
        .filter(HoaDonBan.no_lai > 0)
        .order_by(HoaDonBan.ngay.asc())
        .all()
    )

    result = []

    for hd in hoa_dons:

        so_hd = hd.so_hd if hd.so_hd else str(hd.id)

        result.append({
            "ma_hoa_don": so_hd,
            "ngay": hd.ngay,
            "tong_tien": float(hd.tong_tien or 0),
            "da_tra": float((hd.tong_tien or 0) - (hd.no_lai or 0)),
            "con_no": float(hd.no_lai or 0)
        })

    return result


# =====================================================
# NHẬP HÀNG
# =====================================================
def create_hoa_don_nhap(db: Session, data: HoaDonNhapCreate, user: NhanVien):

    try:

        tong_tien = Decimal("0")

        hoa_don = HoaDonNhap(
            ngay=data.ngay,
            ma_ncc=data.ma_ncc,
            ma_nv=user.ma_nv,
            ma_kho=data.ma_kho,
            trang_thai="nhap",
            tien_mat=data.tien_mat,
            tien_ck=data.tien_ck
        )

        db.add(hoa_don)
        db.flush()

        for item in data.items:

            thanh_tien = Decimal(str(item.so_luong)) * Decimal(str(item.don_gia))
            tong_tien += thanh_tien

            db.add(HoaDonNhapChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            ))

            db.add(NhatKyKho(
                ngay=datetime.utcnow(),
                ma_sp=item.ma_sp,
                ma_kho=data.ma_kho,
                so_luong=item.so_luong,
                loai="nhap",
                bang_tham_chieu="hoa_don_nhap",
                id_tham_chieu=hoa_don.id
            ))

        hoa_don.tong_tien = tong_tien
        hoa_don.tong_thanh_toan = tong_tien

        db.commit()
        db.refresh(hoa_don)

        return hoa_don

    except Exception as e:
        db.rollback()
        raise e


# =====================================================
# BÁN HÀNG
# =====================================================
def create_hoa_don_ban(db: Session, data: HoaDonBanCreate, user: NhanVien):

    try:

        tong_tien = Decimal("0")

        # ===== KIỂM TRA KHÁCH =====
        kh = db.query(KhachHang).filter(
            KhachHang.ma_kh == data.ma_kh
        ).first()

        if not kh:
            raise HTTPException(400, "Khách hàng không tồn tại")

        # ===== TẠO SỐ HÓA ĐƠN =====
        last_hd = db.query(HoaDonBan).order_by(
            HoaDonBan.id.desc()
        ).first()

        so_moi = 1

        if last_hd and last_hd.so_hd:
            try:
                so_moi = int(last_hd.so_hd.replace("HD", "")) + 1
            except:
                so_moi = last_hd.id + 1

        so_hd = f"HD{so_moi:05d}"

        hoa_don = HoaDonBan(
            so_hd=so_hd,
            ngay=data.ngay,
            ma_kh=data.ma_kh,
            ma_nv=user.ma_nv,
            ma_kho=data.ma_kho,
            tien_mat=data.tien_mat,
            tien_ck=data.tien_ck,
            trang_thai="xac_nhan"
        )

        db.add(hoa_don)
        db.flush()

        # ===== XỬ LÝ SẢN PHẨM =====
        for item in data.items:

            sp = db.query(SanPham).filter(
                SanPham.ma_sp == item.ma_sp
            ).first()

            if not sp:
                raise HTTPException(400, f"Sản phẩm {item.ma_sp} không tồn tại")

            # kiểm tra tồn kho snapshot
            sql = text("""
            SELECT so_luong
            FROM ton_kho_chot_ngay
            WHERE ma_kho = :ma_kho
            AND ma_sp = :ma_sp
            ORDER BY ngay DESC
            LIMIT 1
            """)

            row = db.execute(sql, {
                "ma_kho": data.ma_kho,
                "ma_sp": item.ma_sp
            }).fetchone()

            ton = Decimal(str(row[0])) if row else Decimal("0")

            if ton < Decimal(str(item.so_luong)):
                raise HTTPException(
                    status_code=400,
                    detail=f"Tồn kho không đủ cho {item.ma_sp}"
                )

            thanh_tien = Decimal(str(item.so_luong)) * Decimal(str(item.don_gia))
            tong_tien += thanh_tien

            db.add(HoaDonBanChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            ))

            db.add(NhatKyKho(
                ngay=datetime.utcnow(),
                ma_sp=item.ma_sp,
                ma_kho=data.ma_kho,
                so_luong=item.so_luong,
                loai="xuat",
                bang_tham_chieu="hoa_don_ban",
                id_tham_chieu=hoa_don.id,
                ma_nv=user.ma_nv   # 👈 QUAN TRỌNG
            ))

        # ===== TÍNH TIỀN =====
        tien_mat = Decimal(str(data.tien_mat or 0))
        tien_ck = Decimal(str(data.tien_ck or 0))

        tong_da_tra = tien_mat + tien_ck
        no_moi = tong_tien - tong_da_tra

        hoa_don.tong_tien = tong_tien
        hoa_don.tong_thanh_toan = tong_da_tra
        hoa_don.no_lai = no_moi

        # =========================
        # THU TIỀN MẶT (NV)
        # =========================
        if tien_mat > 0:

            last = (
                db.query(ThuChi)
                .filter(ThuChi.ma_nv == user.ma_nv)
                .order_by(ThuChi.id.desc())
                .first()
            )

            so_du_hien_tai = float(last.so_du_sau) if last else 0
            so_du_moi = so_du_hien_tai + float(tien_mat)

            db.add(ThuChi(
                ngay=datetime.utcnow(),
                ma_nv=user.ma_nv,
                doi_tuong="nhan_vien",
                loai="thu",
                loai_giao_dich="ban_hang",
                so_tien=float(tien_mat),
                hinh_thuc="tien_mat",
                so_du_sau=so_du_moi,
                ngay_tao=datetime.utcnow(),
                noi_dung=f"Thu tiền mặt HĐ {so_hd}"
            ))

        # =========================
        # THU CHUYỂN KHOẢN (CÔNG TY)
        # =========================
        if tien_ck > 0:

            db.add(ThuChi(
                ngay=datetime.utcnow(),
                ma_nv=user.ma_nv,
                doi_tuong="cong_ty",
                loai="thu",
                loai_giao_dich="ban_hang",
                so_tien=float(tien_ck),
                hinh_thuc="chuyen_khoan",
                ngay_tao=datetime.utcnow(),
                noi_dung=f"Thu CK HĐ {so_hd}"
            ))

        db.commit()
        db.refresh(hoa_don)

        return hoa_don

    except Exception as e:
        db.rollback()
        raise e
