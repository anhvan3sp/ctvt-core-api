from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from sqlalchemy import text
from app.database import get_db
from app.models import ThuChi, QuyNhanVienChotNgay, QuyCongTyChotNgay
from app.auth_utils import get_current_user
from app.schemas import ThuChiCreate

router = APIRouter(prefix="/thu-chi-nv", tags=["thu_chi_nhan_vien"])


THU_TYPES = [
    "khach_tra_no",
    "khach_dat_hang",
    "cho_hang_thue",
    "thu_khac"
]

CHI_TYPES = [
    "do_dau",
    "sua_xe",
    "dang_kiem",
    "tien_doi",
    "nop_tien",   # 👈 thêm
    "chi_khac"
]




@router.post("/create")
def create_thu_chi_nv(
    data: ThuChiCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    if data.loai == "thu" and data.loai_giao_dich not in THU_TYPES:
        raise HTTPException(400, "loai_giao_dich không hợp lệ")

    if data.loai == "chi" and data.loai_giao_dich not in CHI_TYPES:
        raise HTTPException(400, "loai_giao_dich không hợp lệ")

    with db.begin():

        # ==============================
        # LOCK QUỸ NHÂN VIÊN
        # ==============================
        row = db.execute(text("""
            SELECT so_du_sau
            FROM thu_chi
            WHERE doi_tuong = 'nhan_vien'
            AND ma_nv = :ma_nv
            ORDER BY id DESC
            LIMIT 1
            FOR UPDATE
        """), {"ma_nv": user.ma_nv}).fetchone()

        so_du_hien_tai = float(row[0]) if row else 0

        # ==============================
        # CASE: NỘP TIỀN
        # ==============================
        if data.loai == "chi" and data.loai_giao_dich == "nop_tien":

            if so_du_hien_tai < data.so_tien:
                raise HTTPException(400, "Không đủ tiền")

            so_du_nv_moi = so_du_hien_tai - data.so_tien

            # LOCK QUỸ CÔNG TY
            row_ct = db.execute(text("""
                SELECT so_du_ct_sau
                FROM thu_chi
                WHERE doi_tuong = 'cong_ty'
                ORDER BY id DESC
                LIMIT 1
                FOR UPDATE
            """)).fetchone()

            so_du_ct = float(row_ct[0]) if row_ct else 0
            so_du_ct_moi = so_du_ct + data.so_tien

            # 1. TRỪ NV
            db.execute(text("""
                INSERT INTO thu_chi (
                    ngay, doi_tuong, ma_nv,
                    so_tien, loai, hinh_thuc,
                    loai_giao_dich, noi_dung,
                    so_du_sau
                )
                VALUES (
                    NOW(), 'nhan_vien', :ma_nv,
                    :so_tien, 'chi', :hinh_thuc,
                    'nop_tien', 'Nộp tiền về công ty',
                    :so_du
                )
            """), {
                "ma_nv": user.ma_nv,
                "so_tien": data.so_tien,
                "hinh_thuc": data.hinh_thuc,
                "so_du": so_du_nv_moi
            })

            # 2. CỘNG CÔNG TY
            db.execute(text("""
                INSERT INTO thu_chi (
                    ngay, doi_tuong,
                    so_tien, loai, hinh_thuc,
                    loai_giao_dich, noi_dung,
                    so_du_ct_sau
                )
                VALUES (
                    NOW(), 'cong_ty',
                    :so_tien, 'thu', :hinh_thuc,
                    'nop_tien', :noi_dung,
                    :so_du
                )
            """), {
                "so_tien": data.so_tien,
                "hinh_thuc": data.hinh_thuc,
                "noi_dung": f"{user.ma_nv} nộp tiền",
                "so_du": so_du_ct_moi
            })

            return {"message": "Nộp tiền OK", "so_du": so_du_nv_moi}

        # ==============================
        # CASE BÌNH THƯỜNG
        # ==============================
        if data.loai == "thu":
            so_du_moi = so_du_hien_tai + data.so_tien
        else:
            if so_du_hien_tai < data.so_tien:
                raise HTTPException(400, "Không đủ tiền")
            so_du_moi = so_du_hien_tai - data.so_tien

        db.execute(text("""
            INSERT INTO thu_chi (
                ngay, doi_tuong, ma_nv,
                so_tien, loai, hinh_thuc,
                loai_giao_dich, so_du_sau
            )
            VALUES (
                NOW(), 'nhan_vien', :ma_nv,
                :so_tien, :loai, :hinh_thuc,
                :loai_gd, :so_du
            )
        """), {
            "ma_nv": user.ma_nv,
            "so_tien": data.so_tien,
            "loai": data.loai,
            "hinh_thuc": data.hinh_thuc,
            "loai_gd": data.loai_giao_dich,
            "so_du": so_du_moi
        })

    return {"message": "ok", "so_du": so_du_moi}
    return {
        "message": "ok",
        "so_du": so_du_moi
    }
