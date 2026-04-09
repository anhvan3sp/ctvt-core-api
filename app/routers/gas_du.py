from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.auth_utils import require_roles

from app.models import HoaDonGasDu
from app.services import create_gas_du_service, confirm_gas_du_service
from app.schemas import GasDuCreate  # 🔥 dùng schema

router = APIRouter(prefix="/gas-du", tags=["gas-du"])


# =====================================================
# CREATE GAS DƯ
# =====================================================
@router.post("")
def create_gas_du(
    payload: GasDuCreate,   # 🔥 FIX: dùng schema
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nhan_vien"]))
):
    try:
        return create_gas_du_service(db, payload.dict(), user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# =====================================================
# CONFIRM GAS DƯ
# =====================================================
@router.post("/{id}/confirm")
def confirm_gas_du(
    id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nhan_vien"]))
):
    try:
        return confirm_gas_du_service(db, id, user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# =====================================================
# LIST HÓA ĐƠN GAS DƯ
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
            "ma_kho": r.ma_kho,   # 🔥 FIX: thêm kho
            "tong_tien": float(r.tong_tien or 0),
            "tien_mat": float(r.tien_mat or 0),
            "tien_ck": float(r.tien_ck or 0),
            "trang_thai": r.trang_thai,
            "created_at": r.created_at
        }
        for r in rows
    ]


# =====================================================
# DETAIL (QUAN TRỌNG – DEBUG & UI)
# =====================================================
@router.get("/{id}")
def get_gas_du_detail(
    id: int,
    db: Session = Depends(get_db),
):
    hd = db.query(HoaDonGasDu).filter_by(id=id).first()

    if not hd:
        raise HTTPException(404, "Không tìm thấy")

    return {
        "id": hd.id,
        "ma_kho": hd.ma_kho,
        "tong_tien": float(hd.tong_tien or 0),
        "trang_thai": hd.trang_thai,
        "items": [
            {
                "ma_sp_vo": i.ma_sp_vo,
                "so_luong_vo": float(i.so_luong_vo),
                "tong_kg": float(i.tong_kg),
                "kg_ban": float(i.kg_ban),
                "kg_du": float(i.kg_du),
                "don_gia": float(i.don_gia),
                "thanh_tien": float(i.thanh_tien),
            }
            for i in hd.chi_tiet
        ]
    }
