from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.auth_utils import require_roles

from app.models import GasDu, HoaDonGasDu
from app.services import (
    create_gas_du_service,
    confirm_gas_du_service,
)

router = APIRouter(prefix="/gas-du", tags=["gas-du"])


# =====================================================
# TẠO HÓA ĐƠN GAS DƯ (NHÁP)
# =====================================================
@router.post("")
def create_gas_du(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nhan_vien"]))
):
    try:
        result = create_gas_du_service(db, payload, user)
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


# =====================================================
# CONFIRM HÓA ĐƠN GAS DƯ (QUAN TRỌNG NHẤT)
# =====================================================
@router.post("/{id}/confirm")
def confirm_gas_du(
    id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nhan_vien"]))
):
    try:
        result = confirm_gas_du_service(db, id, user)
        db.commit()
        return result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


# =====================================================
# DANH SÁCH HÓA ĐƠN GAS DƯ
# =====================================================
@router.get("")
def get_list_gas_du(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(HoaDonGasDu)
        .order_by(desc(HoaDonGasDu.id))
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "ma_hd": r.ma_hd,
            "tong_tien": float(r.tong_tien or 0),
            "tien_mat": float(r.tien_mat or 0),
            "tien_ck": float(r.tien_ck or 0),
            "trang_thai": r.trang_thai,
            "created_at": r.created_at
        }
        for r in rows
    ]


# =====================================================
# CHI TIẾT HÓA ĐƠN
# =====================================================
@router.get("/{id}")
def get_gas_du_detail(
    id: int,
    db: Session = Depends(get_db),
):
    hd = db.query(HoaDonGasDu).filter(HoaDonGasDu.id == id).first()

    if not hd:
        raise HTTPException(404, "Không tìm thấy hóa đơn")

    return {
        "id": hd.id,
        "ma_hd": hd.ma_hd,
        "tong_tien": float(hd.tong_tien or 0),
        "tien_mat": float(hd.tien_mat or 0),
        "tien_ck": float(hd.tien_ck or 0),
        "trang_thai": hd.trang_thai,
        "created_at": hd.created_at
    }


# =====================================================
# LẤY TỒN GAS DƯ
# =====================================================
@router.get("/ton")
def get_gas_du_ton(
    ma_sp_goc: str,
    ma_kho: str,
    db: Session = Depends(get_db),
):
    row = (
        db.query(GasDu)
        .filter(
            GasDu.ma_sp_goc == ma_sp_goc,
            GasDu.ma_kho == ma_kho
        )
        .order_by(desc(GasDu.id))
        .first()
    )

    return {
        "ma_sp_goc": ma_sp_goc,
        "ma_kho": ma_kho,
        "ton_kg": float(row.ton_sau_kg) if row else 0
    }


# =====================================================
# LỊCH SỬ GAS DƯ (LEDGER)
# =====================================================
@router.get("/lich-su")
def get_gas_du_history(
    ma_sp_goc: str,
    ma_kho: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(GasDu)
        .filter(
            GasDu.ma_sp_goc == ma_sp_goc,
            GasDu.ma_kho == ma_kho
        )
        .order_by(desc(GasDu.id))
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "thoi_diem": r.thoi_diem,
            "loai": r.loai,
            "so_kg": float(r.so_kg),
            "ton_sau_kg": float(r.ton_sau_kg),
            "ref_type": r.ref_type,
            "ref_id": r.ref_id,
            "ghi_chu": r.ghi_chu
        }
        for r in rows
    ]
