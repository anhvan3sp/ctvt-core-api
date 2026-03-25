from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from app.database import get_db
from app.models import (
    ThuChi,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay
)
from app.auth_utils import get_current_user
from app.schemas import ThuChiCreate

router = APIRouter(prefix="/thu-chi-nv", tags=["thu_chi_nhan_vien"])


# ====== CONST ======
VALID_GD = {
    "tien_do",
    "do_dau",
    "nop_tien",
    "chi_khac",
    "thu_khac",
    "sua_xe",
    "dang_kiem",
    "nop_them",
    "chuyen_tien_vao_NH"
}


def to_decimal(val):
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError):
        raise HTTPException(400, "Số tiền không hợp lệ")


@router.post("/create")
def create_thu_chi(
    data: ThuChiCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:

        # =========================
        # 0. IDEMPOTENCY (FAST CHECK)
        # =========================
        if data.idempotency_key:
            existed = db.query(ThuChi).filter_by(
                idempotency_key=data.idempotency_key
            ).first()

            if existed:
                return {
                    "msg": "DUPLICATE",
                    "id": existed.id,
                    "so_du_nv": float(existed.so_du_sau or 0),
                    "tong_quy": float(existed.so_du_ct_sau or 0)
                }

        # =========================
        # 1. VALIDATE
        # =========================
        if data.loai_giao_dich not in VALID_GD:
            raise HTTPException(400, f"Loại giao dịch không hợp lệ: {data.loai_giao_dich}")

        so_tien = to_decimal(data.so_tien)

        if so_tien <= 0:
            raise HTTPException(400, "Số tiền phải > 0")

        # =========================
        # 1.5 DUPLICATE CHECK (🔥 NEW)
        # =========================
        # check trong 10 giây gần nhất
        existed = db.query(ThuChi).filter(
            ThuChi.ma_nv == user.ma_nv,
            ThuChi.so_tien == so_tien,
            ThuChi.loai == data.loai,
            ThuChi.loai_giao_dich == data.loai_giao_dich,
            ThuChi.ngay >= datetime.now() - timedelta(seconds=10)
        ).first()

        # nếu trùng và chưa force → báo
        if existed and not getattr(data, "force", False):
            raise HTTPException(409, "GIAO_DICH_TRUNG")

        # =========================
        # 2. LOCK QUỸ
        # =========================
        quy_ct = db.query(QuyCongTyChotNgay).with_for_update().first()

        if not quy_ct:
            raise HTTPException(400, "Chưa có quỹ công ty")

        quy_nv = None
        is_admin = user.ma_nv == "admin"

        if not is_admin:
            quy_nv = db.query(QuyNhanVienChotNgay)\
                .filter_by(ma_nv=user.ma_nv)\
                .with_for_update()\
                .first()

            if not quy_nv:
                raise HTTPException(400, "Chưa có quỹ nhân viên")

        # =========================
        # 3. NGHIỆP VỤ
        # =========================
        if not is_admin:

            if data.loai_giao_dich == "nop_tien":

                if quy_nv.so_du < so_tien:
                    raise HTTPException(400, "Không đủ tiền")

                quy_nv.so_du -= so_tien
                quy_ct.tien_mat += so_tien

            elif data.loai == "chi":

                if quy_nv.so_du < so_tien:
                    raise HTTPException(400, "Không đủ tiền")

                quy_nv.so_du -= so_tien

            elif data.loai == "thu":

                if data.hinh_thuc == "tien_mat":
                    quy_nv.so_du += so_tien
                else:
                    quy_ct.tien_ngan_hang += so_tien

            else:
                raise HTTPException(400, "Sai loại thu chi")

        else:

            if data.loai_giao_dich == "chuyen_tien_vao_NH":

                if quy_ct.tien_mat < so_tien:
                    raise HTTPException(400, "Không đủ tiền")

                quy_ct.tien_mat -= so_tien
                quy_ct.tien_ngan_hang += so_tien

            else:
                raise HTTPException(400, "Admin chỉ được chuyển tiền")

        # =========================
        # 4. UPDATE QUỸ
        # =========================
        quy_ct.tong_quy = quy_ct.tien_mat + quy_ct.tien_ngan_hang

        # =========================
        # 5. CREATE RECORD
        # =========================
        record = ThuChi(
            ngay=datetime.now(),
            doi_tuong="cong_ty" if is_admin else "nhan_vien",
            ma_nv=user.ma_nv,
            so_tien=so_tien,
            loai=data.loai,
            hinh_thuc=data.hinh_thuc,
            loai_giao_dich=data.loai_giao_dich,
            ma_kh=None,
            ma_ncc=None,
            so_du_sau=quy_nv.so_du if quy_nv else Decimal("0"),
            so_du_ct_sau=quy_ct.tong_quy,
            idempotency_key=data.idempotency_key,
            created_by=user.ma_nv
        )

        db.add(record)

        # =========================
        # 6. COMMIT SAFE
        # =========================
        try:
            db.commit()
        except IntegrityError:
            db.rollback()

            existed = db.query(ThuChi).filter_by(
                idempotency_key=data.idempotency_key
            ).first()

            if existed:
                return {
                    "msg": "DUPLICATE",
                    "id": existed.id,
                    "so_du_nv": float(existed.so_du_sau or 0),
                    "tong_quy": float(existed.so_du_ct_sau or 0)
                }

            raise HTTPException(500, "Lỗi duplicate")

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

    return {
        "msg": "OK",
        "so_du_nv": float(quy_nv.so_du) if quy_nv else 0,
        "tong_quy": float(quy_ct.tong_quy)
    }
