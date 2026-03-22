from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.auth_utils import get_current_user
from app.models import (
    TonKhoChotNgay,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    ThuChi
)

from app.schemas import KhoiTaoDauKyRequest

router = APIRouter(prefix="/system", tags=["system"])


# =========================
# HELPER
# =========================
def check_duplicate(items, keys):
    seen = set()
    for item in items:
        key = tuple(getattr(item, k) for k in keys)
        if key in seen:
            raise HTTPException(400, f"Trùng dữ liệu: {key}")
        seen.add(key)


def validate_data(payload):
    # ===== TỒN KHO =====
    for x in payload.ton_kho:
        if not x.ma_kho or not x.ma_sp:
            raise HTTPException(400, "Thiếu mã kho hoặc sản phẩm")
        if x.so_luong < 0:
            raise HTTPException(400, "Số lượng không được âm")

    check_duplicate(payload.ton_kho, ["ma_kho", "ma_sp"])

    # ===== QUỸ NV =====
    for x in payload.quy_nhan_vien:
        if not x.ma_nv:
            raise HTTPException(400, "Thiếu mã nhân viên")
        if x.so_du < 0:
            raise HTTPException(400, "Số dư không được âm")

    check_duplicate(payload.quy_nhan_vien, ["ma_nv"])

    # ===== CÔNG NỢ KH =====
    for x in payload.cong_no_khach:
        if not x.ma_kh:
            raise HTTPException(400, "Thiếu mã khách hàng")
        if x.so_no < 0:
            raise HTTPException(400, "Công nợ không được âm")

    check_duplicate(payload.cong_no_khach, ["ma_kh"])

    # ===== CÔNG NỢ NCC =====
    for x in payload.cong_no_ncc:
        if not x.ma_ncc:
            raise HTTPException(400, "Thiếu mã NCC")
        if x.so_no < 0:
            raise HTTPException(400, "Công nợ không được âm")

    check_duplicate(payload.cong_no_ncc, ["ma_ncc"])


# =========================
# DANH MỤC (FIX UX)
# =========================
@router.get("/danh-muc")
def get_danh_muc(db: Session = Depends(get_db)):
    return {
        "kho": [
            {"ma_kho": x[0], "ten_kho": x[0]}
            for x in db.execute(text("SELECT ma_kho FROM kho_hang"))
        ],
        "san_pham": [
            {"ma_sp": x[0], "ten_sp": x[0]}
            for x in db.execute(text("SELECT ma_sp FROM san_pham"))
        ],
        "nhan_vien": [
            {"ma_nv": x[0], "ten_nv": x[0]}
            for x in db.execute(text("SELECT ma_nv FROM nhan_vien"))
        ],
        "khach_hang": [
            {
                "ma_kh": x[0],
                "ten_kh": x[1]  # 🔥 hiển thị tên
            }
            for x in db.execute(text("""
                SELECT ma_kh, ten_cua_hang FROM khach_hang
            """))
        ],
        "ncc": [
            {"ma_ncc": x[0], "ten_ncc": x[0]}
            for x in db.execute(text("SELECT ma_ncc FROM nha_cung_cap"))
        ],
    }


# =========================
# POST
# =========================
@router.post("/dau-ky")
def save_dau_ky(
    payload: KhoiTaoDauKyRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.vai_tro != "admin":
        raise HTTPException(403, "Chỉ admin")

    try:
        # ===== VALIDATE =====
        validate_data(payload)

        # ===== HARD LOCK =====
        if db.query(ThuChi).count() > 0:
            raise HTTPException(400, "Đã có giao dịch")

        # ===== RESET =====
        db.query(TonKhoChotNgay).delete()
        db.query(QuyNhanVienChotNgay).delete()
        db.query(QuyCongTyChotNgay).delete()

        db.execute(text("DELETE FROM cong_no_khach_hang"))
        db.execute(text("DELETE FROM cong_no_ncc"))

        # ===== TON KHO =====
        if payload.ton_kho:
            db.execute(text("""
                INSERT INTO ton_kho_chot_ngay (ma_kho, ma_sp, so_luong)
                VALUES (:ma_kho, :ma_sp, :so_luong)
            """), [x.dict() for x in payload.ton_kho])

        # ===== QUỸ NV =====
        if payload.quy_nhan_vien:
            db.execute(text("""
                INSERT INTO quy_nhan_vien_chot_ngay (ma_nv, so_du)
                VALUES (:ma_nv, :so_du)
            """), [x.dict() for x in payload.quy_nhan_vien])

        # ===== QUỸ CTY =====
        db.add(QuyCongTyChotNgay(
            tien_mat=payload.quy_cong_ty.tien_mat,
            tien_ngan_hang=payload.quy_cong_ty.tien_ngan_hang,
            tong_quy=payload.quy_cong_ty.tien_mat + payload.quy_cong_ty.tien_ngan_hang
        ))

        # ===== CÔNG NỢ KH =====
        if payload.cong_no_khach:
            db.execute(text("""
                INSERT INTO cong_no_khach_hang (ma_kh, so_du)
                VALUES (:ma_kh, :so_no)
            """), [x.dict() for x in payload.cong_no_khach])

        # ===== CÔNG NỢ NCC =====
        if payload.cong_no_ncc:
            db.execute(text("""
                INSERT INTO cong_no_ncc (ma_ncc, so_du)
                VALUES (:ma_ncc, :so_no)
            """), [x.dict() for x in payload.cong_no_ncc])

        db.commit()

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

    return {"status": "success"}
