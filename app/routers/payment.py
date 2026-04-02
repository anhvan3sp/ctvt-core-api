from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal, InvalidOperation
from datetime import datetime

from app.database import get_db
from app.models import (
    ThuChi,
    CongNoKhachHang,
    CongNoKhachHangLog,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay
)
from app.auth_utils import get_current_user
from app.schemas import PaymentCreate

router = APIRouter(prefix="/payment", tags=["payment"])


# =========================
# UTILS
# =========================
def to_decimal(val):
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError):
        raise HTTPException(400, "Số tiền không hợp lệ")


def now_vn():
    return datetime.utcnow().replace(microsecond=0)


# =========================
# CREATE PAYMENT
# =========================
@router.post("/")
def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        now = now_vn()

        # =========================
        # IDEMPOTENCY
        # =========================
        if data.idempotency_key:
            existed = db.query(ThuChi).filter_by(
                idempotency_key=data.idempotency_key
            ).first()

            if existed:
                return {
                    "msg": "DUPLICATE",
                    "id": existed.id
                }

        # =========================
        # VALIDATE
        # =========================
        tien_mat = to_decimal(data.tien_mat or 0)
        tien_ck = to_decimal(data.tien_ck or 0)

        tong_tien = tien_mat + tien_ck

        if tong_tien <= 0:
            raise HTTPException(400, "Số tiền phải > 0")

        # =========================
        # LOCK CÔNG NỢ
        # =========================
        cn = db.query(CongNoKhachHang)\
            .filter_by(ma_kh=data.ma_kh)\
            .with_for_update()\
            .first()

        if not cn:
            cn = CongNoKhachHang(
                ma_kh=data.ma_kh,
                so_du=Decimal("0")
            )
            db.add(cn)
            db.flush()

        # =========================
        # LOCK QUỸ
        # =========================
        quy_nv = db.query(QuyNhanVienChotNgay)\
            .filter_by(ma_nv=user.ma_nv)\
            .with_for_update()\
            .first()

        quy_ct = db.query(QuyCongTyChotNgay)\
            .with_for_update()\
            .first()

        if not quy_nv or not quy_ct:
            raise HTTPException(500, "Chưa có dữ liệu quỹ")

        # =========================
        # UPDATE CÔNG NỢ
        # =========================
        # 🔥 luôn giảm nợ
        cn.so_du -= tong_tien

        db.add(CongNoKhachHangLog(
            ma_kh=data.ma_kh,
            ngay=now,
            phat_sinh=-tong_tien,
            loai="payment"
        ))

        # =========================
        # UPDATE QUỸ
        # =========================
        if tien_mat > 0:
            quy_nv.so_du += tien_mat

        if tien_ck > 0:
            quy_ct.tien_ngan_hang += tien_ck

        # =========================
        # THU CHI (LEDGER)
        # =========================
        if tien_mat > 0:
            db.add(ThuChi(
                ngay=now,
                doi_tuong="nhan_vien",
                ma_nv=user.ma_nv,
                so_tien=tien_mat,
                loai="thu",
                hinh_thuc="tien_mat",
                loai_giao_dich="khach_tra_no",
                noi_dung=data.noi_dung,
                ma_kh=data.ma_kh,
                idempotency_key=data.idempotency_key,
                created_by=user.ma_nv,
                so_du_sau=quy_nv.so_du
            ))

        if tien_ck > 0:
            db.add(ThuChi(
                ngay=now,
                doi_tuong="cong_ty",
                ma_nv=user.ma_nv,
                so_tien=tien_ck,
                loai="thu",
                hinh_thuc="chuyen_khoan",
                loai_giao_dich="khach_tra_no",
                noi_dung=data.noi_dung,
                ma_kh=data.ma_kh,
                idempotency_key=data.idempotency_key,
                created_by=user.ma_nv,
                so_du_ct_sau=quy_ct.tien_ngan_hang
            ))

        db.commit()

        return {
            "msg": "PAYMENT_OK",
            "cong_no": float(cn.so_du)
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Trùng idempotency_key")

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
