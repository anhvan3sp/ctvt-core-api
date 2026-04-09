from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.auth_utils import require_roles

from app.models import GasDu, HoaDonGasDu
from app.services import create_gas_du_service, confirm_gas_du_service

router = APIRouter(prefix="/gas-du", tags=["gas-du"])


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
