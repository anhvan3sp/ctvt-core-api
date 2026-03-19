from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models import ThuChi, QuyNhanVienChotNgay, QuyCongTyChotNgay
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
        # LOCK QUỸ NHÂN VIÊN
        # =========================
        quy_nv = db.query(QuyNhanVienChotNgay)\
            .filter_by(ma_nv=user.ma_nv)\
            .with_for_update()\
            .first()

        if not quy_nv:
            raise HTTPException(400, "Chưa có quỹ nhân viên")

        so_du_hien_tai = float(quy_nv.so_du)

        # =========================
        # LOCK QUỸ CÔNG TY
        # =========================
        quy_ct = db.query(QuyCongTyChotNgay)\
            .with_for_update()\
            .first()

        if not quy_ct:
            raise HTTPException(400, "Chưa có quỹ công ty")

        # =========================
        # CASE: NỘP TIỀN
        # =========================
        if data.loai == "chi" and data.loai_giao_dich == "nop_tien":

            if so_du_hien_tai < data.so_tien:
                raise HTTPException(400, "Không đủ tiền")

            # trừ NV
            quy_nv.so_du -= data.so_tien

            # cộng CT
            if data.hinh_thuc == "tien_mat":
                quy_ct.tien_mat += data.so_tien
            else:
                quy_ct.tien_ngan_hang += data.so_tien

        else:

            if data.loai == "thu":
                quy_nv.so_du += data.so_tien
            else:
                if so_du_hien_tai < data.so_tien:
                    raise HTTPException(400, "Không đủ tiền")
                quy_nv.so_du -= data.so_tien

        # =========================
        # UPDATE TỔNG CÔNG TY
        # =========================
        quy_ct.tong_quy = quy_ct.tien_mat + quy_ct.tien_ngan_hang

        # =========================
        # INSERT LOG
        # =========================
        tc = ThuChi(
            ma_nv=user.ma_nv,
            loai=data.loai,
            so_tien=data.so_tien,
            hinh_thuc=data.hinh_thuc,
            loai_giao_dich=data.loai_giao_dich,
            so_du_sau=quy_nv.so_du,
            so_du_ct_sau=quy_ct.tong_quy
        )

        db.add(tc)

    return {
        "message": "OK",
        "so_du": quy_nv.so_du
    }
