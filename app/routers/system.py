from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date

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
# DANH MỤC
# =========================
@router.get("/danh-muc")
def get_danh_muc(db: Session = Depends(get_db)):
    return {
        "kho": [x[0] for x in db.execute(text("SELECT ma_kho FROM kho_hang"))],
        "san_pham": [x[0] for x in db.execute(text("SELECT ma_sp FROM san_pham"))],
        "nhan_vien": [x[0] for x in db.execute(text("SELECT ma_nv FROM nhan_vien"))],
        "khach_hang": [x[0] for x in db.execute(text("SELECT ma_kh FROM khach_hang"))],
        "ncc": [x[0] for x in db.execute(text("SELECT ma_ncc FROM nha_cung_cap"))],
    }


# =========================
# GET
# =========================
@router.get("/dau-ky")
def get_dau_ky(db: Session = Depends(get_db)):

    ton_kho = db.query(TonKhoChotNgay).all()
    quy_nv = db.query(QuyNhanVienChotNgay).all()
    quy_ct = db.query(QuyCongTyChotNgay).first()

    cong_no_khach = db.execute(text("""
        SELECT ma_kh, so_du FROM cong_no_khach_hang
    """)).fetchall()

    cong_no_ncc = db.execute(text("""
        SELECT ma_ncc, so_du FROM cong_no_ncc
    """)).fetchall()

    return {
        "ton_kho": [
            {
                "ma_kho": x.ma_kho,
                "ma_sp": x.ma_sp,
                "so_luong": float(x.so_luong)
            }
            for x in ton_kho
        ],
        "quy_nhan_vien": [
            {
                "ma_nv": x.ma_nv,
                "so_du": float(x.so_du)
            }
            for x in quy_nv
        ],
        "quy_cong_ty": {
            "tien_mat": float(quy_ct.tien_mat) if quy_ct else 0,
            "tien_ngan_hang": float(quy_ct.tien_ngan_hang) if quy_ct else 0
        },
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
    payload: KhoiTaoDauKyRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.vai_tro != "admin":
        raise HTTPException(403, "Chỉ admin")

    # ===== FIX: nếu thiếu ngày thì auto lấy hôm nay =====
    ngay = payload.ngay or date.today().isoformat()

    with db.begin():

        # ===== HARD LOCK =====
        if db.query(ThuChi).count() > 0:
            raise HTTPException(400, "Đã có giao dịch")

        # ======================
        # RESET
        # ======================
        db.query(TonKhoChotNgay).delete()
        db.query(QuyNhanVienChotNgay).delete()
        db.query(QuyCongTyChotNgay).delete()

        db.execute(text("DELETE FROM cong_no_khach_hang"))
        db.execute(text("DELETE FROM cong_no_ncc"))

        # ======================
        # TON KHO
        # ======================
        if payload.ton_kho:
            db.execute(text("""
                INSERT INTO ton_kho_chot_ngay (ngay, ma_kho, ma_sp, so_luong)
                VALUES (:ngay, :ma_kho, :ma_sp, :so_luong)
            """), [
                {
                    "ngay": ngay,
                    "ma_kho": x.ma_kho,
                    "ma_sp": x.ma_sp,
                    "so_luong": x.so_luong
                }
                for x in payload.ton_kho
            ])

        # ======================
        # QUỸ NV
        # ======================
        if payload.quy_nhan_vien:
            db.execute(text("""
                INSERT INTO quy_nhan_vien_chot_ngay (ngay, ma_nv, so_du)
                VALUES (:ngay, :ma_nv, :so_du)
            """), [
                {
                    "ngay": ngay,
                    "ma_nv": x.ma_nv,
                    "so_du": x.so_du
                }
                for x in payload.quy_nhan_vien
            ])

        # ======================
        # QUỸ CÔNG TY (FIX CHÍ MẠNG)
        # ======================
        db.add(QuyCongTyChotNgay(
            ngay=ngay,
            tien_mat=payload.quy_cong_ty.tien_mat,
            tien_ngan_hang=payload.quy_cong_ty.tien_ngan_hang,
            tong_quy=payload.quy_cong_ty.tien_mat + payload.quy_cong_ty.tien_ngan_hang
        ))

        # ======================
        # CÔNG NỢ KHÁCH
        # ======================
        if payload.cong_no_khach:
            db.execute(text("""
                INSERT INTO cong_no_khach_hang (ma_kh, so_du)
                VALUES (:ma_kh, :so_no)
            """), [
                {
                    "ma_kh": x.ma_kh,
                    "so_no": x.so_no
                }
                for x in payload.cong_no_khach
            ])

        # ======================
        # CÔNG NỢ NCC
        # ======================
        if payload.cong_no_ncc:
            db.execute(text("""
                INSERT INTO cong_no_ncc (ma_ncc, so_du)
                VALUES (:ma_ncc, :so_no)
            """), [
                {
                    "ma_ncc": x.ma_ncc,
                    "so_no": x.so_no
                }
                for x in payload.cong_no_ncc
            ])

    return {"status": "success"}
