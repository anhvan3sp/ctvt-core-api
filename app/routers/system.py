from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth_utils import get_current_user
from app.models import (
    TonKhoChotNgay,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    ThuChi
)

# 🔥 DÙNG SCHEMA GỐC
from app.schemas import KhoiTaoDauKyRequest

router = APIRouter(prefix="/system", tags=["system"])


# =========================
# DANH MỤC (dropdown)
# =========================
@router.get("/danh-muc")
def get_danh_muc(db: Session = Depends(get_db)):

    return {
        "kho": [x[0] for x in db.execute("SELECT ma_kho FROM kho_hang")],
        "san_pham": [x[0] for x in db.execute("SELECT ma_sp FROM san_pham")],
        "nhan_vien": [x[0] for x in db.execute("SELECT ma_nv FROM nhan_vien")],
        "khach_hang": [x[0] for x in db.execute("SELECT ma_kh FROM khach_hang")],
        "ncc": [x[0] for x in db.execute("SELECT ma_ncc FROM nha_cung_cap")]
    }


# =========================
# GET
# =========================
@router.get("/dau-ky")
def get_dau_ky(db: Session = Depends(get_db)):

    ton_kho = db.query(TonKhoChotNgay).all()
    quy_nv = db.query(QuyNhanVienChotNgay).all()
    quy_ct = db.query(QuyCongTyChotNgay).first()

    cong_no_khach = db.execute(
        "SELECT ma_kh, so_du FROM cong_no_khach_hang"
    ).fetchall()

    cong_no_ncc = db.execute(
        "SELECT ma_ncc, so_du FROM cong_no_ncc"
    ).fetchall()

    return {
        "ton_kho": [
            {"ma_kho": x.ma_kho, "ma_sp": x.ma_sp, "so_luong": float(x.so_luong)}
            for x in ton_kho
        ],
        "quy_nhan_vien": [
            {"ma_nv": x.ma_nv, "so_du": float(x.so_du)}
            for x in quy_nv
        ],
        "quy_cong_ty": {
            "tien_mat": float(quy_ct.tien_mat) if quy_ct else 0,
            "tien_ngan_hang": float(quy_ct.tien_ngan_hang) if quy_ct else 0
        },
        # 🔥 FRONTEND đang dùng so_no → map lại
        "cong_no_khach": [
            {"ma_kh": x[0], "so_no": float(x[1])}
            for x in cong_no_khach
        ],
        "cong_no_ncc": [
            {"ma_ncc": x[0], "so_no": float(x[1])}
            for x in cong_no_ncc
        ]
    }


# =========================
# POST
# =========================
@router.post("/dau-ky")
def save_dau_ky(
    payload: KhoiTaoDauKyRequest,   # 🔥 FIX CHUẨN
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.vai_tro != "admin":
        raise HTTPException(403, "Chỉ admin")

    with db.begin():

        # 🔥 HARD LOCK
        if db.query(ThuChi).count() > 0:
            raise HTTPException(400, "Đã có giao dịch")

        # ======================
        # RESET
        # ======================
        db.query(TonKhoChotNgay).delete()
        db.query(QuyNhanVienChotNgay).delete()
        db.query(QuyCongTyChotNgay).delete()

        db.execute("DELETE FROM cong_no_khach_hang")
        db.execute("DELETE FROM cong_no_ncc")

        # ======================
        # TON KHO
        # ======================
        if payload.ton_kho:
            db.execute("""
                INSERT INTO ton_kho_chot_ngay (ma_kho, ma_sp, so_luong)
                VALUES (:ma_kho, :ma_sp, :so_luong)
            """, [x.dict() for x in payload.ton_kho])

        # ======================
        # QUỸ NV
        # ======================
        if payload.quy_nhan_vien:
            db.execute("""
                INSERT INTO quy_nhan_vien_chot_ngay (ma_nv, so_du)
                VALUES (:ma_nv, :so_du)
            """, [x.dict() for x in payload.quy_nhan_vien])

        # ======================
        # QUỸ CTY (schema cũ: 1 số)
        # ======================
        db.add(QuyCongTyChotNgay(
            tien_mat=payload.quy_cong_ty,
            tien_ngan_hang=0,
            tong_quy=payload.quy_cong_ty
        ))

        # ======================
        # CÔNG NỢ KHÁCH
        # ======================
        if payload.cong_no_khach:
            db.execute("""
                INSERT INTO cong_no_khach_hang (ma_kh, so_du)
                VALUES (:ma_kh, :so_no)
            """, [x.dict() for x in payload.cong_no_khach])

        # ======================
        # CÔNG NỢ NCC
        # ======================
        if payload.cong_no_ncc:
            db.execute("""
                INSERT INTO cong_no_ncc (ma_ncc, so_du)
                VALUES (:ma_ncc, :so_no)
            """, [x.dict() for x in payload.cong_no_ncc])

    return {"status": "success"}
