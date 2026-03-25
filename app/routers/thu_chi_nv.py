from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.database import get_db
from app.models import (
    ThuChi,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    KhachHang,
    NhaCungCap
)
from app.auth_utils import get_current_user
from app.schemas import ThuChiCreate

router = APIRouter(prefix="/thu-chi-nv", tags=["thu_chi_nhan_vien"])


# ====== CONST (SYNC WITH DB) ======
VALID_GD = {
    "khach_dat_hang"
    "tien_do",
    "nhap_hang",
    "ban_hang",
    "do_dau",
    "nop_tien",
    "khach_tra_no",
    "tra_no_ncc",
    "chuyen_khoan",
    "nop_them",
    "chi_khac",
    "nop_them_quy",
    "chuyen_tien_vao_NH",
    "thu_khac",

    # bổ sung FE đang dùng
    "sua_xe",
    "dang_kiem"
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
        # VALIDATE
        # =========================
        if data.loai_giao_dich not in VALID_GD:
            raise HTTPException(400, f"Loại giao dịch không hợp lệ: {data.loai_giao_dich}")

        so_tien = to_decimal(data.so_tien)

        if so_tien <= 0:
            raise HTTPException(400, "Số tiền phải > 0")

        # =========================
        # LOCK QUỸ
        # =========================
        quy_ct = db.query(QuyCongTyChotNgay).with_for_update().first()

        if not quy_ct:
            raise HTTPException(400, "Chưa có quỹ công ty")

        quy_nv = None

        if user.ma_nv != "admin":
            quy_nv = db.query(QuyNhanVienChotNgay)\
                .filter_by(ma_nv=user.ma_nv)\
                .with_for_update()\
                .first()

            if not quy_nv:
                raise HTTPException(400, "Chưa có quỹ nhân viên")

        # =========================
        # ===== NHÂN VIÊN =====
        # =========================
        if user.ma_nv != "admin":

            if data.loai_giao_dich == "nop_tien":

                if quy_nv.so_du < so_tien:
                    raise HTTPException(400, "Không đủ tiền")

                quy_nv.so_du -= so_tien
                quy_ct.tien_mat += so_tien

            elif data.loai_giao_dich == "khach_tra_no":

                if not data.ma_kh:
                    raise HTTPException(400, "Thiếu mã khách")

                kh = db.query(KhachHang)\
                    .filter_by(ma_kh=data.ma_kh)\
                    .with_for_update()\
                    .first()

                if not kh:
                    raise HTTPException(400, "Không có khách")

                kh.cong_no -= so_tien
                if kh.cong_no < 0:
                    kh.cong_no = 0

                if data.hinh_thuc == "tien_mat":
                    quy_nv.so_du += so_tien
                else:
                    quy_ct.tien_ngan_hang += so_tien

            elif data.loai_giao_dich in ["do_dau", "sua_xe", "dang_kiem", "chi_khac", "tien_do"]:

                if quy_nv.so_du < so_tien:
                    raise HTTPException(400, "Không đủ tiền")

                quy_nv.so_du -= so_tien

            elif data.loai_giao_dich in ["thu_khac", "nop_them"]:
                quy_nv.so_du += so_tien

            else:
                raise HTTPException(400, f"NV không xử lý loại này: {data.loai_giao_dich}")

        # =========================
        # ===== ADMIN =====
        # =========================
        else:

            if data.loai_giao_dich == "nop_tien_cong_ty":

                if data.hinh_thuc == "tien_mat":
                    quy_ct.tien_mat += so_tien
                else:
                    quy_ct.tien_ngan_hang += so_tien

            elif data.loai_giao_dich == "chuyen_tien_vao_NH":

                if quy_ct.tien_mat < so_tien:
                    raise HTTPException(400, "Không đủ tiền mặt")

                quy_ct.tien_mat -= so_tien
                quy_ct.tien_ngan_hang += so_tien

            elif data.loai_giao_dich == "tra_no_ncc":

                if not data.ma_ncc:
                    raise HTTPException(400, "Thiếu NCC")

                ncc = db.query(NhaCungCap)\
                    .filter_by(ma_ncc=data.ma_ncc)\
                    .with_for_update()\
                    .first()

                if not ncc:
                    raise HTTPException(400, "Không có NCC")

                if ncc.cong_no < so_tien:
                    raise HTTPException(400, "Vượt công nợ")

                if data.hinh_thuc == "tien_mat":
                    if quy_ct.tien_mat < so_tien:
                        raise HTTPException(400, "Không đủ tiền")
                    quy_ct.tien_mat -= so_tien
                else:
                    if quy_ct.tien_ngan_hang < so_tien:
                        raise HTTPException(400, "Không đủ tiền CK")
                    quy_ct.tien_ngan_hang -= so_tien

                ncc.cong_no -= so_tien

            else:
                raise HTTPException(400, f"Admin không dùng loại này: {data.loai_giao_dich}")

        # =========================
        # UPDATE QUỸ
        # =========================
        quy_ct.tong_quy = quy_ct.tien_mat + quy_ct.tien_ngan_hang

        # =========================
        # LOG
        # =========================
        db.add(ThuChi(
            ngay=datetime.now(),
            doi_tuong="cong_ty" if user.ma_nv == "admin" else "nhan_vien",
            ma_nv=user.ma_nv,
            so_tien=so_tien,
            loai=data.loai,
            hinh_thuc=data.hinh_thuc,
            loai_giao_dich=data.loai_giao_dich,
            ma_kh=data.ma_kh if data.loai_giao_dich == "khach_tra_no" else None,
            ma_ncc=data.ma_ncc if data.loai_giao_dich == "tra_no_ncc" else None,
            so_du_sau=quy_nv.so_du if quy_nv else Decimal("0"),
            so_du_ct_sau=quy_ct.tong_quy
        ))

        db.commit()

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
