from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.auth_utils import get_current_user

from app.models import (
    TonKhoChotNgay,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay
)

from app.schemas import KhoiTaoDauKyRequest

router = APIRouter(
    prefix="/system",
    tags=["system"]
)


# ====================================================
# KHỞI TẠO DỮ LIỆU ĐẦU KỲ ERP
# ====================================================

@router.post("/khoi-tao-dau-ky")
def khoi_tao_dau_ky(
    data: KhoiTaoDauKyRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    # chỉ admin được phép chạy
    if user.vai_tro != "admin":
        raise HTTPException(403, "Chỉ admin được khởi tạo đầu kỳ")

    ngay = datetime.strptime(data.ngay, "%Y-%m-%d")

    # ==========================================
    # 1. TỒN KHO ĐẦU KỲ
    # ==========================================

    for item in data.ton_kho:

        row = TonKhoChotNgay(
            ngay_chot=ngay,
            ma_sp=item.ma_sp,
            ma_kho=item.ma_kho,
            so_luong=item.so_luong,
            ngay_tao=datetime.now()
        )

        db.add(row)

    # ==========================================
    # 2. QUỸ NHÂN VIÊN ĐẦU KỲ
    # ==========================================

    for q in data.quy_nhan_vien:

        row = QuyNhanVienChotNgay(
            ngay_chot=ngay,
            ma_nv=q.ma_nv,
            so_du=q.so_du,
            so_du_luy_ke=q.so_du,
            ngay_tao=datetime.now()
        )

        db.add(row)

    # ==========================================
    # 3. QUỸ CÔNG TY ĐẦU KỲ
    # ==========================================

    quy_cty = QuyCongTyChotNgay(
        ngay_chot=ngay,
        so_du=data.quy_cong_ty,
        ngay_tao=datetime.now()
    )

    db.add(quy_cty)

    # ==========================================
    # 4. COMMIT
    # ==========================================

    db.commit()

    return {
        "message": "Khởi tạo dữ liệu đầu kỳ thành công",
        "ngay": data.ngay
    }
