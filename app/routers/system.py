from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app.auth_utils import get_current_user
from app.models import (
    TonKhoChotNgay,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    ThuChi
)

router = APIRouter(prefix="/system", tags=["system"])

# ====================================================
# SCHEMA
# ====================================================

class TonKhoItem(BaseModel):
    ma_kho: str
    ma_sp: str
    so_luong: float

class QuyNVItem(BaseModel):
    ma_nv: str
    so_du: float

class QuyCongTyItem(BaseModel):
    tien_mat: float = 0
    tien_ngan_hang: float = 0

class DauKyPayload(BaseModel):
    ton_kho: List[TonKhoItem]
    quy_nhan_vien: List[QuyNVItem]
    quy_cong_ty: QuyCongTyItem


# ====================================================
# GET - LOAD ĐẦU KỲ
# ====================================================

@router.get("/dau-ky")
def get_dau_ky(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
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
        }
    }


# ====================================================
# VALIDATE
# ====================================================

def validate_payload(payload: DauKyPayload):

    errors = []

    # tồn kho
    for i, x in enumerate(payload.ton_kho):
        if not x.ma_sp:
            errors.append(f"ton_kho dòng {i+1}: thiếu mã SP")

        if not x.ma_kho:
            errors.append(f"ton_kho dòng {i+1}: thiếu mã kho")

        if x.so_luong < 0:
            errors.append(f"ton_kho dòng {i+1}: số lượng âm")

    # quỹ NV
    for i, x in enumerate(payload.quy_nhan_vien):
        if not x.ma_nv:
            errors.append(f"quy_nhan_vien dòng {i+1}: thiếu mã NV")

        if x.so_du < 0:
            errors.append(f"quy_nhan_vien dòng {i+1}: số dư âm")

    return errors


# ====================================================
# POST - SAVE ĐẦU KỲ
# ====================================================

@router.post("/dau-ky")
def save_dau_ky(
    payload: DauKyPayload,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.vai_tro != "admin":
        raise HTTPException(403, "Chỉ admin")

    errors = validate_payload(payload)
    if errors:
        return {"status": "error", "errors": errors}

    with db.begin():

        # 🔥 HARD LOCK (CỰC QUAN TRỌNG)
        if db.query(ThuChi).count() > 0:
            raise HTTPException(
                400,
                "Đã phát sinh giao dịch → không được sửa đầu kỳ"
            )

        # ======================
        # RESET
        # ======================
        db.query(TonKhoChotNgay).delete()
        db.query(QuyNhanVienChotNgay).delete()
        db.query(QuyCongTyChotNgay).delete()

        # ======================
        # TON KHO
        # ======================
        if payload.ton_kho:
            db.execute("""
                INSERT INTO ton_kho_chot_ngay (ma_kho, ma_sp, so_luong)
                VALUES (:ma_kho, :ma_sp, :so_luong)
            """, [x.dict() for x in payload.ton_kho])

        # ======================
        # QUỸ NHÂN VIÊN
        # ======================
        if payload.quy_nhan_vien:
            db.execute("""
                INSERT INTO quy_nhan_vien_chot_ngay (ma_nv, so_du)
                VALUES (:ma_nv, :so_du)
            """, [x.dict() for x in payload.quy_nhan_vien])

        # ======================
        # QUỸ CÔNG TY
        # ======================
        tien_mat = payload.quy_cong_ty.tien_mat or 0
        tien_ck = payload.quy_cong_ty.tien_ngan_hang or 0

        db.add(QuyCongTyChotNgay(
            tien_mat=tien_mat,
            tien_ngan_hang=tien_ck,
            tong_quy=tien_mat + tien_ck
        ))

    return {"status": "success"}
