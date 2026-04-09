from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.auth_utils import require_roles

from app.models import GasDu, HoaDonBan
from app.services.gas_du_service import apply_gas_du_from_sale

router = APIRouter(prefix="/gas-du", tags=["gas-du"])


# =====================================================
# APPLY GAS DƯ TỪ SALE (CHÍNH)
# =====================================================
@router.post("/apply-sale")
def apply_gas_du_sale(
    id_hoa_don: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "nhan_vien"]))
):
    try:
        hoa_don = db.query(HoaDonBan).filter(
            HoaDonBan.id == id_hoa_don
        ).first()

        if not hoa_don:
            raise HTTPException(404, "Không tìm thấy hóa đơn")

        if hoa_don.trang_thai != "xac_nhan":
            raise HTTPException(400, "Phải xác nhận hóa đơn trước")

        items = payload.get("items", [])

        if not items:
            raise HTTPException(400, "Không có dữ liệu gas dư")

        apply_gas_du_from_sale(
            db,
            hoa_don=hoa_don,
            items=items
        )

        db.commit()

        return {"msg": "APPLY_GAS_DU_OK"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


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
# LỊCH SỬ GAS DƯ
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
            "ghi_chu": r.ghi_chu
        }
        for r in rows
    ]
