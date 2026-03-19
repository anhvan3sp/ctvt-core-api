from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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


@router.post("/create")
def create_thu_chi_nv(
    data: ThuChiCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    with db.begin():

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

        if not quy_ct:
            raise HTTPException(400, "Chưa có quỹ công ty")

        so_tien = data.so_tien

        # =========================
        # NHÂN VIÊN
        # =========================
        if user.ma_nv != "admin":

            if not quy_nv:
                raise HTTPException(400, "Chưa có quỹ NV")

            # ----------------------
            # NỘP TIỀN
            # ----------------------
            if data.loai == "chi" and data.loai_giao_dich == "nop_tien":

                if quy_nv.so_du < so_tien:
                    raise HTTPException(400, "Không đủ tiền")

                quy_nv.so_du -= so_tien
                quy_ct.tien_mat += so_tien

            # ----------------------
            # THU NỢ KHÁCH
            # ----------------------
            elif data.loai_giao_dich == "khach_tra_no":

                kh = db.query(KhachHang)\
                    .filter_by(ma_kh=data.ma_kh)\
                    .with_for_update()\
                    .first()

                if not kh:
                    raise HTTPException(400, "Không có khách")

                kh.cong_no = (kh.cong_no or 0) - so_tien
                if kh.cong_no < 0:
                    kh.cong_no = 0

                if data.hinh_thuc == "tien_mat":
                    quy_nv.so_du += so_tien
                else:
                    quy_ct.tien_ngan_hang += so_tien

            # ----------------------
            # CHI BÌNH THƯỜNG
            # ----------------------
            elif data.loai == "chi":

                if quy_nv.so_du < so_tien:
                    raise HTTPException(400, "Không đủ tiền")

                quy_nv.so_du -= so_tien

            # ----------------------
            # THU KHÁC
            # ----------------------
            elif data.loai == "thu":
                quy_nv.so_du += so_tien

        # =========================
        # ADMIN
        # =========================
        else:

            # ----------------------
            # CHUYỂN TIỀN MẶT → CK
            # ----------------------
            if data.loai_giao_dich == "chuyen_khoan":

                if quy_ct.tien_mat < so_tien:
                    raise HTTPException(400, "Không đủ tiền mặt")

                quy_ct.tien_mat -= so_tien
                quy_ct.tien_ngan_hang += so_tien

            # ----------------------
            # NỘP THÊM TIỀN (tăng quỹ)
            # ----------------------
            elif data.loai_giao_dich == "nop_them":

                if data.hinh_thuc == "tien_mat":
                    quy_ct.tien_mat += so_tien
                else:
                    quy_ct.tien_ngan_hang += so_tien

            # ----------------------
            # THANH TOÁN NCC
            # ----------------------
            elif data.loai_giao_dich == "tra_no_ncc":

                ncc = db.query(NhaCungCap)\
                    .filter_by(ma_ncc=data.ma_ncc)\
                    .with_for_update()\
                    .first()

                if not ncc:
                    raise HTTPException(400, "Không có NCC")

                if ncc.cong_no < so_tien:
                    raise HTTPException(400, "Số tiền vượt nợ")

                if data.hinh_thuc == "tien_mat":
                    if quy_ct.tien_mat < so_tien:
                        raise HTTPException(400, "Không đủ tiền")
                    quy_ct.tien_mat -= so_tien
                else:
                    if quy_ct.tien_ngan_hang < so_tien:
                        raise HTTPException(400, "Không đủ tiền CK")
                    quy_ct.tien_ngan_hang -= so_tien

                ncc.cong_no -= so_tien

        # =========================
        # UPDATE TỔNG
        # =========================
        quy_ct.tong_quy = quy_ct.tien_mat + quy_ct.tien_ngan_hang

        # =========================
        # LOG
        # =========================
        db.add(ThuChi(
            ma_nv=user.ma_nv,
            loai=data.loai,
            loai_giao_dich=data.loai_giao_dich,
            so_tien=so_tien,
            hinh_thuc=data.hinh_thuc,
            so_du_sau=quy_nv.so_du if quy_nv else 0,
            so_du_ct_sau=quy_ct.tong_quy
        ))

    return {
        "message": "OK",
        "so_du_nv": quy_nv.so_du if quy_nv else 0,
        "tong_quy": quy_ct.tong_quy
    }
