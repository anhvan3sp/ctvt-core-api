from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, timedelta
import uuid

from app.database import get_db
from app.models import PhatSinh, TrangThaiPhatSinh
from app.schemas import (
    PhatSinhCreate,
    PhatSinhConfirm,
    PhatSinhCancel,
    ThuChiCreate
)
from app.auth_utils import get_current_user

# 🔥 gọi lại API thu_chi
from app.routers.thu_chi_nv import create_thu_chi

router = APIRouter(prefix="/phat-sinh", tags=["phat_sinh"])


# =========================
# 🔥 TIME VN (CHUẨN TOÀN HỆ)
# =========================
def now_vn():
    return datetime.utcnow() + timedelta(hours=7)


# =========================
# CREATE (NHÁP) + WARNING TRÙNG
# =========================
@router.post("/create")
def create_phat_sinh(
    data: PhatSinhCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    now = now_vn()

    # =========================
    # CHECK TRÙNG (CHỈ WARNING)
    # =========================
    existing = db.query(PhatSinh).filter(
        PhatSinh.ma_nv == user.ma_nv,
        PhatSinh.loai == data.loai,
        PhatSinh.loai_giao_dich == data.loai_giao_dich,
        PhatSinh.so_tien == data.so_tien,
        PhatSinh.ngay == now.date(),
        PhatSinh.trang_thai != TrangThaiPhatSinh.HUY
    ).order_by(PhatSinh.thoi_diem.desc()).first()

    if existing and not getattr(data, "force", False):
        return {
            "warning": True,
            "message": f"Giao dịch giống đã tồn tại lúc {existing.thoi_diem.strftime('%H:%M:%S')}",
            "existing_id": existing.id
        }

    # =========================
    # CREATE
    # =========================
    ps = PhatSinh(
        ma_nv=user.ma_nv,
        ngay=now.date(),
        thoi_diem=now,
        loai=data.loai,
        loai_giao_dich=data.loai_giao_dich,
        so_tien=data.so_tien,
        dien_giai=data.dien_giai,
        trang_thai=TrangThaiPhatSinh.NHAP,
        created_at=now,
        updated_at=now
    )

    db.add(ps)
    db.commit()
    db.refresh(ps)

    return ps


# =========================
# CONFIRM (🔥 FIX: KHÔNG CHECK TRÙNG)
# =========================
@router.post("/confirm")
def confirm_phat_sinh(
    data: PhatSinhConfirm,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        now = now_vn()

        ps = db.execute(
            select(PhatSinh)
            .where(PhatSinh.id == data.id)
            .with_for_update()
        ).scalar_one_or_none()

        if not ps:
            raise HTTPException(404, "Không tìm thấy")

        # idempotent
        if ps.trang_thai == TrangThaiPhatSinh.XAC_NHAN:
            return {"msg": "ALREADY_CONFIRMED"}

        if ps.trang_thai != TrangThaiPhatSinh.NHAP:
            raise HTTPException(400, "Đã xác nhận hoặc huỷ")

        # =========================
        # ❌ KHÔNG CÒN CHECK TRÙNG Ở ĐÂY
        # =========================

        idem_key = f"ps_confirm_{ps.id}"

        tc_data = ThuChiCreate(
            loai=ps.loai,
            loai_giao_dich=ps.loai_giao_dich,
            so_tien=float(ps.so_tien),
            hinh_thuc="tien_mat",
            noi_dung=f"PS #{ps.id} - {ps.dien_giai or ''}",
            idempotency_key=idem_key
        )

        result = create_thu_chi(tc_data, db, user)

        ps.trang_thai = TrangThaiPhatSinh.XAC_NHAN
        ps.idempotency_key = idem_key
        ps.updated_at = now

        db.commit()

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

    return {
        "msg": "XAC_NHAN_OK",
        "data": result
    }


# =========================
# CANCEL (REVERSAL)
# =========================
@router.post("/cancel")
def cancel_phat_sinh(
    data: PhatSinhCancel,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        now = now_vn()

        ps = db.execute(
            select(PhatSinh)
            .where(PhatSinh.id == data.id)
            .with_for_update()
        ).scalar_one_or_none()

        if not ps:
            raise HTTPException(404, "Không tìm thấy")

        if ps.trang_thai == TrangThaiPhatSinh.HUY:
            return {"msg": "ALREADY_CANCELED"}

        if ps.trang_thai != TrangThaiPhatSinh.XAC_NHAN:
            raise HTTPException(400, "Chỉ huỷ khi đã xác nhận")

        loai_dao = "thu" if ps.loai == "chi" else "chi"

        idem_key = f"ps_cancel_{ps.id}"

        tc_data = ThuChiCreate(
            loai=loai_dao,
            loai_giao_dich=ps.loai_giao_dich,
            so_tien=float(ps.so_tien),
            hinh_thuc="tien_mat",
            noi_dung=f"HUY PS #{ps.id}",
            idempotency_key=idem_key
        )

        result = create_thu_chi(tc_data, db, user)

        ps.trang_thai = TrangThaiPhatSinh.HUY
        ps.updated_at = now

        db.commit()

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

    return {
        "msg": "HUY_OK",
        "data": result
    }


# =========================
# DELETE (🔥 FIX 404)
# =========================
@router.post("/delete")
def delete_phat_sinh(
    data: PhatSinhConfirm,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        ps = db.query(PhatSinh).filter(
            PhatSinh.id == data.id,
            PhatSinh.ma_nv == user.ma_nv
        ).first()

        if not ps:
            raise HTTPException(404, "Không tìm thấy")

        if ps.trang_thai != TrangThaiPhatSinh.NHAP:
            raise HTTPException(400, "Chỉ được xoá nháp")

        db.delete(ps)
        db.commit()

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

    return {"msg": "DELETED"}


# =========================
# LIST TODAY
# =========================
@router.get("/today")
def get_today(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    today = now_vn().date()

    result = db.query(PhatSinh).filter(
        PhatSinh.ma_nv == user.ma_nv,
        PhatSinh.ngay == today
    ).order_by(PhatSinh.id.desc()).all()

    return result
