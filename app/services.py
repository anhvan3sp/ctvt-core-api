from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc
from decimal import Decimal
from app.models import HoaDonGasDuChiTiet  # nhớ import
from fastapi import HTTPException
from datetime import datetime, timedelta


from app.models import (
    HoaDonNhap,
    HoaDonNhapChiTiet,
    HoaDonBan,
    HoaDonBanChiTiet,
    NhatKyKho,
    ThuChi,
    NhanVien,
    KhachHang,
    SanPham,
    GasDu, HoaDonGasDu
)

from app.schemas import HoaDonNhapCreate, HoaDonBanCreate

# =====================================================
# TIME VN
# =====================================================

def now_vn():
    return datetime.utcnow() + timedelta(hours=7)


# =====================================================
# CORE GAS DƯ (LEDGER)
# =====================================================
def apply_gas_du(
    db: Session,
    *,
    ma_sp_goc: str,
    ma_kho: str,
    delta_kg: float,
    loai: str,
    ref_id: int = None,
    ref_type: str = "gas_du",   # FIX
    ma_kh: str = None,
    ma_nv: str = None,
    ghi_chu: str = None,
):
    delta_kg = Decimal(str(delta_kg))

    last_row = (
        db.query(GasDu)
        .filter(
            GasDu.ma_sp_goc == ma_sp_goc,
            GasDu.ma_kho == ma_kho,
        )
        .order_by(desc(GasDu.id))
        .with_for_update()
        .first()
    )

    ton_truoc = last_row.ton_sau_kg if last_row else Decimal("0")
    ton_moi = ton_truoc + delta_kg

    if ton_moi < 0:
        raise HTTPException(400, f"Không đủ gas dư: {ma_sp_goc}")

    db.add(GasDu(
        thoi_diem=now_vn(),
        loai=loai,
        ma_sp_goc=ma_sp_goc,
        ma_kho=ma_kho,
        so_kg=delta_kg,
        ton_sau_kg=ton_moi,
        ref_type="gas_du",
        ref_id=ref_id,
        ma_kh=ma_kh,
        ma_nv=ma_nv,
        ghi_chu=ghi_chu,
        created_at=now_vn(),
    ))

def create_gas_du_service(db: Session, payload: dict, user):

    items = payload.get("items", [])
    ma_kho = payload.get("ma_kho")

    if not items:
        raise HTTPException(400, "Không có sản phẩm")

    hoa_don = HoaDonGasDu(
        ma_kho=ma_kho,
        tien_mat=payload.get("tien_mat", 0),
        tien_ck=payload.get("tien_ck", 0),
        trang_thai="nhap",
        created_at=now_vn()
    )

    db.add(hoa_don)
    db.flush()

    tong_tien = Decimal("0")

    

    for item in items:
        so_luong_vo = Decimal(str(item["so_luong_vo"]))
        quy_doi_kg = Decimal(str(item["quy_doi_kg"]))
        don_gia = Decimal(str(item["don_gia"]))
        kg_ban = Decimal(str(item["kg_ban"]))
    
        tong_kg = so_luong_vo * quy_doi_kg
    
        if kg_ban < 0 or kg_ban > tong_kg:
            raise HTTPException(400, "kg_ban không hợp lệ")
    
        kg_du = tong_kg - kg_ban
        thanh_tien = kg_ban * don_gia   # 🔥 FIX
    
        tong_tien += thanh_tien
    
        db.add(HoaDonGasDuChiTiet(
            id_hoa_don=hoa_don.id,
            ma_sp_vo=item["ma_sp_vo"],
            so_luong_vo=so_luong_vo,
            quy_doi_kg=quy_doi_kg,
            tong_kg=tong_kg,
            kg_ban=kg_ban,     # 🔥 thêm
            kg_du=kg_du,       # 🔥 thêm
            don_gia=don_gia,
            thanh_tien=thanh_tien
        ))
    

    hoa_don.tong_tien = tong_tien

    return {
        "id": hoa_don.id,
        "tong_tien": float(tong_tien)
    }

def confirm_gas_du_service(db, id, user):

    hd = db.query(HoaDonGasDu).filter_by(id=id).first()

    if not hd:
        raise Exception("Không tìm thấy")

    if hd.trang_thai == "xac_nhan":
        raise Exception("Đã confirm")

    items = hd.items  # nếu có relationship

    for item in items:

        tong_kg = item.so_luong_vo * item.quy_doi_kg
        kg_ban = item.kg_ban
        kg_du = tong_kg - kg_ban

        # 1. trừ bình
        db.execute("""
            UPDATE ton_kho_chot_ngay
            SET so_luong = so_luong - :sl
            WHERE ma_sp = :ma_sp AND ma_kho = :kho
        """, {
            "sl": item.so_luong_vo,
            "ma_sp": item.ma_sp_vo,
            "kho": hd.ma_kho
        })

        # 2. cộng gas dư
        apply_gas_du(
            db,
            ma_sp_goc=item.ma_sp_vo,
            ma_kho=hd.ma_kho,
            delta_kg=kg_du,
            loai="phat_sinh",
            ref_id=hd.id
        )

        # 3. bán gas dư
        apply_gas_du(
            db,
            ma_sp_goc=item.ma_sp_vo,
            ma_kho=hd.ma_kho,
            delta_kg=-kg_ban,
            loai="ban",
            ref_id=hd.id
        )

    hd.trang_thai = "xac_nhan"


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

    if not data.items:
        raise HTTPException(400, "Không có sản phẩm")

    with db.begin():

        tong_tien = Decimal("0")

        # =========================
        # TÍNH TỔNG TRƯỚC (KHÔNG TIN FRONTEND)
        # =========================
        for item in data.items:
            tong_tien += Decimal(str(item.so_luong)) * Decimal(str(item.don_gia))

        tien_mat = Decimal(str(data.tien_mat or 0))
        tien_ck = Decimal(str(data.tien_ck or 0))

        if tien_mat + tien_ck > tong_tien:
            raise HTTPException(400, "Tiền lớn hơn tổng")

        # =========================
        # TẠO HÓA ĐƠN
        # =========================
        hoa_don = HoaDonNhap(
            ngay=datetime.utcnow(),   # ✅ FIX: backend tự set
            ma_ncc=data.ma_ncc,
            ma_nv=user.ma_nv,
            ma_kho=data.ma_kho,
            trang_thai="nhap",
            tien_mat=tien_mat,
            tien_ck=tien_ck
        )

        db.add(hoa_don)
        db.flush()

        # =========================
        # XỬ LÝ ITEMS
        # =========================
        for item in data.items:

            thanh_tien = Decimal(str(item.so_luong)) * Decimal(str(item.don_gia))

            db.add(HoaDonNhapChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            ))

            # nhật ký kho
            db.add(NhatKyKho(
                ngay=datetime.utcnow(),
                ma_sp=item.ma_sp,
                ma_kho=data.ma_kho,
                so_luong=item.so_luong,
                loai="nhap",
                bang_tham_chieu="hoa_don_nhap",
                id_tham_chieu=hoa_don.id,
                ma_nv=user.ma_nv   # ✅ FIX thiếu field
            ))

        # =========================
        # UPDATE HÓA ĐƠN
        # =========================
        hoa_don.tong_tien = tong_tien
        hoa_don.tong_thanh_toan = tong_tien

        return hoa_don

# =====================================================
# BÁN HÀNG
# =====================================================


def create_hoa_don_ban(db: Session, data: HoaDonBanCreate, user: NhanVien):

    with db.begin():

        tong_tien = Decimal("0")

        # ===== CHECK KH =====
        kh = db.query(KhachHang).filter(
            KhachHang.ma_kh == data.ma_kh
        ).first()

        if not kh:
            raise HTTPException(400, "Khách hàng không tồn tại")

        # ===== TẠO SỐ HĐ =====
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

        # =========================
        # XỬ LÝ SẢN PHẨM (LOCK KHO)
        # =========================
        for item in data.items:

            # LOCK tồn kho
            row = db.execute(text("""
                SELECT so_luong
                FROM ton_kho_chot_ngay
                WHERE ma_kho = :ma_kho
                AND ma_sp = :ma_sp
                FOR UPDATE
            """), {
                "ma_kho": data.ma_kho,
                "ma_sp": item.ma_sp
            }).fetchone()

            ton = Decimal(str(row[0])) if row else Decimal("0")

            if ton < Decimal(str(item.so_luong)):
                raise HTTPException(400, f"Tồn kho không đủ {item.ma_sp}")

            # TRỪ KHO NGAY (balance realtime)
            db.execute(text("""
                UPDATE ton_kho_chot_ngay
                SET so_luong = so_luong - :sl
                WHERE ma_kho = :ma_kho
                AND ma_sp = :ma_sp
            """), {
                "sl": item.so_luong,
                "ma_kho": data.ma_kho,
                "ma_sp": item.ma_sp
            })

            thanh_tien = Decimal(str(item.so_luong)) * Decimal(str(item.don_gia))
            tong_tien += thanh_tien

            db.add(HoaDonBanChiTiet(
                id_hoa_don=hoa_don.id,
                ma_sp=item.ma_sp,
                so_luong=item.so_luong,
                don_gia=item.don_gia,
                thanh_tien=thanh_tien
            ))

            # ledger kho
            db.add(NhatKyKho(
                ngay=datetime.utcnow(),
                ma_sp=item.ma_sp,
                ma_kho=data.ma_kho,
                so_luong=item.so_luong,
                loai="xuat",
                bang_tham_chieu="hoa_don_ban",
                id_tham_chieu=hoa_don.id,
                ma_nv=user.ma_nv
            ))

        # =========================
        # TÍNH TIỀN
        # =========================
        tien_mat = Decimal(str(data.tien_mat or 0))
        tien_ck = Decimal(str(data.tien_ck or 0))
        tong_da_tra = tien_mat + tien_ck
        no_moi = tong_tien - tong_da_tra

        hoa_don.tong_tien = tong_tien
        hoa_don.tong_thanh_toan = tong_da_tra
        hoa_don.no_lai = no_moi

        # =========================
        # THU TIỀN MẶT (NV) - LOCK
        # =========================
        if tien_mat > 0:

            row = db.execute(text("""
                SELECT so_du_sau
                FROM thu_chi
                WHERE doi_tuong = 'nhan_vien'
                AND ma_nv = :ma_nv
                ORDER BY id DESC
                LIMIT 1
                FOR UPDATE
            """), {"ma_nv": user.ma_nv}).fetchone()

            so_du = float(row[0]) if row else 0
            so_du_moi = so_du + float(tien_mat)

            db.execute(text("""
                INSERT INTO thu_chi (
                    ngay, doi_tuong, ma_nv,
                    so_tien, loai, hinh_thuc,
                    loai_giao_dich, so_du_sau
                )
                VALUES (
                    NOW(), 'nhan_vien', :ma_nv,
                    :tien, 'thu', 'tien_mat',
                    'ban_hang', :so_du
                )
            """), {
                "ma_nv": user.ma_nv,
                "tien": float(tien_mat),
                "so_du": so_du_moi
            })

        # =========================
        # THU CK (CÔNG TY) - LOCK
        # =========================
        if tien_ck > 0:

            row = db.execute(text("""
                SELECT so_du_ct_sau
                FROM thu_chi
                WHERE doi_tuong = 'cong_ty'
                ORDER BY id DESC
                LIMIT 1
                FOR UPDATE
            """)).fetchone()

            so_du_ct = float(row[0]) if row else 0
            so_du_ct_moi = so_du_ct + float(tien_ck)

            db.execute(text("""
                INSERT INTO thu_chi (
                    ngay, doi_tuong,
                    so_tien, loai, hinh_thuc,
                    loai_giao_dich, so_du_ct_sau
                )
                VALUES (
                    NOW(), 'cong_ty',
                    :tien, 'thu', 'chuyen_khoan',
                    'ban_hang', :so_du
                )
            """), {
                "tien": float(tien_ck),
                "so_du": so_du_ct_moi
            })

        return hoa_don
