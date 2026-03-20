from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.auth_utils import get_current_user
from app.models import (
    TonKhoChotNgay,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    ThuChi
)

from app.schemas import (
    DauKyPayload
)

router = APIRouter(prefix="/system", tags=["system"])


# =========================================
# DANH MỤC (CHO DROPDOWN)
# =========================================
@router.get("/danh-muc")
def get_danh_muc(db: Session = Depends(get_db)):

    kho = db.execute("SELECT ma_kho FROM kho_hang").fetchall()
    sp = db.execute("SELECT ma_sp FROM san_pham").fetchall()
    nv = db.execute("SELECT ma_nv FROM nhan_vien").fetchall()
    kh = db.execute("SELECT ma_kh FROM khach_hang").fetchall()

    return {
        "kho": [x[0] for x in kho],
        "san_pham": [x[0] for x in sp],
        "nhan_vien": [x[0] for x in nv],
        "khach_hang": [x[0] for x in kh]
    }


# =========================================
# GET
# =========================================
@router.get("/dau-ky")
def get_dau_ky(db: Session = Depends(get_db)):

    ton_kho = db.query(TonKhoChotNgay).all()
    quy_nv = db.query(QuyNhanVienChotNgay).all()
    quy_ct = db.query(QuyCongTyChotNgay).first()

    return {
        "ton_kho": [
            {
                "ma_kho": x.ma_kho,
                "ma_sp": x.ma_sp,
                "so_luong": float(x.so_luong)
            } for x in ton_kho
        ],
        "quy_nhan_vien": [
            {
                "ma_nv": x.ma_nv,
                "so_du": float(x.so_du)
            } for x in quy_nv
        ],
        "quy_cong_ty": {
            "tien_mat": float(quy_ct.tien_mat) if quy_ct else 0,
            "tien_ngan_hang": float(quy_ct.tien_ngan_hang) if quy_ct else 0
        },
        "cong_no": []  # placeholder (sau mở rộng)
    }


# =========================================
# POST
# =========================================
@router.post("/dau-ky")
def save_dau_ky(
    payload: DauKyPayload,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.vai_tro != "admin":
        raise HTTPException(403, "Chỉ admin")

    with db.begin():

        if db.query(ThuChi).count() > 0:
            raise HTTPException(400, "Đã có giao dịch")

        db.query(TonKhoChotNgay).delete()
        db.query(QuyNhanVienChotNgay).delete()
        db.query(QuyCongTyChotNgay).delete()

        if payload.ton_kho:
            db.execute("""
                INSERT INTO ton_kho_chot_ngay (ma_kho, ma_sp, so_luong)
                VALUES (:ma_kho, :ma_sp, :so_luong)
            """, [x.dict() for x in payload.ton_kho])

        if payload.quy_nhan_vien:
            db.execute("""
                INSERT INTO quy_nhan_vien_chot_ngay (ma_nv, so_du)
                VALUES (:ma_nv, :so_du)
            """, [x.dict() for x in payload.quy_nhan_vien])

        db.add(QuyCongTyChotNgay(
            tien_mat=payload.quy_cong_ty.tien_mat,
            tien_ngan_hang=payload.quy_cong_ty.tien_ngan_hang,
            tong_quy=payload.quy_cong_ty.tien_mat + payload.quy_cong_ty.tien_ngan_hang
        ))

    return {"status": "success"}
