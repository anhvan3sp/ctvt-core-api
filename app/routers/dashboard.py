from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app.models import ThuChi, NhatKyKho
from app.auth_utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    # ================================
    # TIMEZONE VIỆT NAM
    # ================================
    now = datetime.utcnow() + timedelta(hours=7)
    start = datetime(now.year, now.month, now.day)
    end = start + timedelta(days=1)

    # =====================================================
    # ADMIN → TOÀN CÔNG TY
    # =====================================================
    if user.ma_nv == "admin":

        # -------- BÁN HÔM NAY --------
        ban_hom_nay = db.query(
            func.coalesce(func.sum(NhatKyKho.so_luong), 0)
        ).filter(
            NhatKyKho.loai == "xuat",
            NhatKyKho.ngay >= start,
            NhatKyKho.ngay < end
        ).scalar() or 0

        # =====================================================
        # QUỸ CÔNG TY (LẤY SỐ DƯ CUỐI - CHUẨN ERP)
        # =====================================================
        last = db.query(ThuChi).order_by(ThuChi.id.desc()).first()

        tong_quy = float(last.so_du_ct_sau) if last and last.so_du_ct_sau else 0

        # 👉 đơn giản hóa (chưa tách tiền mặt / ngân hàng)
        tien_mat = tong_quy
        tien_ngan_hang = 0

        # -------- THU HÔM NAY --------
        thu = db.query(
            func.coalesce(func.sum(ThuChi.so_tien), 0)
        ).filter(
            ThuChi.loai == "thu",
            ThuChi.ngay >= start,
            ThuChi.ngay < end
        ).scalar() or 0

        # -------- CHI HÔM NAY --------
        chi = db.query(
            func.coalesce(func.sum(ThuChi.so_tien), 0)
        ).filter(
            ThuChi.loai == "chi",
            ThuChi.ngay >= start,
            ThuChi.ngay < end
        ).scalar() or 0

        return {
            "loai": "cong_ty",
            "ban_hom_nay": float(ban_hom_nay),
            "tien_mat": float(tien_mat),
            "tien_ngan_hang": float(tien_ngan_hang),
            "tong_quy": float(tong_quy),
            "thu_hom_nay": float(thu),
            "chi_hom_nay": float(chi)
        }

    # =====================================================
    # NHÂN VIÊN
    # =====================================================
    else:

        # -------- BÁN HÔM NAY --------
        ban_hom_nay = db.query(
            func.coalesce(func.sum(NhatKyKho.so_luong), 0)
        ).filter(
            NhatKyKho.loai == "xuat",
            NhatKyKho.ma_nv == user.ma_nv,
            NhatKyKho.ngay >= start,
            NhatKyKho.ngay < end
        ).scalar() or 0

        # =====================================================
        # SỐ DƯ NHÂN VIÊN (LẤY DÒNG CUỐI)
        # =====================================================
        last = db.query(ThuChi).filter(
            ThuChi.ma_nv == user.ma_nv
        ).order_by(ThuChi.id.desc()).first()

        so_du = float(last.so_du_sau) if last and last.so_du_sau else 0

        # -------- THU --------
        thu = db.query(
            func.coalesce(func.sum(ThuChi.so_tien), 0)
        ).filter(
            ThuChi.ma_nv == user.ma_nv,
            ThuChi.loai == "thu",
            ThuChi.ngay >= start,
            ThuChi.ngay < end
        ).scalar() or 0

        # -------- CHI --------
        chi = db.query(
            func.coalesce(func.sum(ThuChi.so_tien), 0)
        ).filter(
            ThuChi.ma_nv == user.ma_nv,
            ThuChi.loai == "chi",
            ThuChi.ngay >= start,
            ThuChi.ngay < end
        ).scalar() or 0

        return {
            "loai": "nhan_vien",
            "ban_hom_nay": float(ban_hom_nay),
            "so_du": float(so_du),
            "thu_hom_nay": float(thu),
            "chi_hom_nay": float(chi)
        }
