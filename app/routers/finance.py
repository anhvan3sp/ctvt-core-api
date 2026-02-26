from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from decimal import Decimal
from datetime import datetime, date

from app.database import get_db
from app.models import ThuChi, HoaDonBan, HoaDonNhap
from app.auth_utils import require_roles, get_current_user
from app.schemas import ThuChiCreate, ThuChiResponse, NopQuyRequest


router = APIRouter(prefix="/finance", tags=["Finance"])


# =====================================================
# GHI THU CHI CHUẨN
# =====================================================
@router.post("/thu-chi", response_model=ThuChiResponse)
def create_thu_chi(
    data: ThuChiCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    - Admin, kế toán: có thể ghi cho công ty
    - nv_dac_biet: mặc định ghi cho chính mình
    """

    doi_tuong = data.doi_tuong

    if user.vai_tro == "nv_dac_biet":
        doi_tuong = "nhan_vien"

    if data.so_tien <= 0:
        raise HTTPException(status_code=400, detail="Số tiền phải > 0")

    thu_chi = ThuChi(
        ngay=data.ngay,
        doi_tuong=doi_tuong,
        ma_nv=user.ma_nv,
        so_tien=data.so_tien,
        loai=data.loai,
        hinh_thuc=data.hinh_thuc,
        noi_dung=data.noi_dung
    )

    db.add(thu_chi)
    db.commit()
    db.refresh(thu_chi)

    return thu_chi


# =====================================================
# QUỸ CÔNG TY (TÁCH TIỀN MẶT / NGÂN HÀNG)
# =====================================================
@router.get("/quy-cong-ty")
def xem_quy_cong_ty(
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "ke_toan"]))
):

    tien_mat = db.query(
        func.coalesce(
            func.sum(
                case(
                    (ThuChi.loai == "thu", ThuChi.so_tien),
                    else_=-ThuChi.so_tien
                )
            ), 0
        )
    ).filter(
        ThuChi.doi_tuong == "cong_ty",
        ThuChi.hinh_thuc == "tien_mat"
    ).scalar()

    tien_ck = db.query(
        func.coalesce(
            func.sum(
                case(
                    (ThuChi.loai == "thu", ThuChi.so_tien),
                    else_=-ThuChi.so_tien
                )
            ), 0
        )
    ).filter(
        ThuChi.doi_tuong == "cong_ty",
        ThuChi.hinh_thuc == "chuyen_khoan"
    ).scalar()

    return {
        "tien_mat": Decimal(str(tien_mat)),
        "tien_ngan_hang": Decimal(str(tien_ck)),
        "tong": Decimal(str(tien_mat)) + Decimal(str(tien_ck))
    }


# =====================================================
# QUỸ NHÂN VIÊN (TÁCH TIỀN MẶT / NGÂN HÀNG)
# =====================================================
@router.get("/quy-nhan-vien")
def xem_quy_nhan_vien(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    tien_mat = db.query(
        func.coalesce(
            func.sum(
                case(
                    (ThuChi.loai == "thu", ThuChi.so_tien),
                    else_=-ThuChi.so_tien
                )
            ), 0
        )
    ).filter(
        ThuChi.doi_tuong == "nhan_vien",
        ThuChi.ma_nv == user.ma_nv,
        ThuChi.hinh_thuc == "tien_mat"
    ).scalar()

    tien_ck = db.query(
        func.coalesce(
            func.sum(
                case(
                    (ThuChi.loai == "thu", ThuChi.so_tien),
                    else_=-ThuChi.so_tien
                )
            ), 0
        )
    ).filter(
        ThuChi.doi_tuong == "nhan_vien",
        ThuChi.ma_nv == user.ma_nv,
        ThuChi.hinh_thuc == "chuyen_khoan"
    ).scalar()

    return {
        "tien_mat": Decimal(str(tien_mat)),
        "tien_ngan_hang": Decimal(str(tien_ck)),
        "tong": Decimal(str(tien_mat)) + Decimal(str(tien_ck))
    }


# =====================================================
# NỘP QUỸ (nv_dac_biet → công ty)
# =====================================================
@router.post("/nop-quy")
def nop_quy(
    data: NopQuyRequest,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["nv_dac_biet"]))
):

    if data.so_tien <= 0:
        raise HTTPException(status_code=400, detail="Số tiền phải > 0")

    # Ghi trừ quỹ nhân viên
    db.add(ThuChi(
        ngay=datetime.utcnow(),
        doi_tuong="nhan_vien",
        ma_nv=user.ma_nv,
        so_tien=data.so_tien,
        loai="chi",
        hinh_thuc=data.hinh_thuc,
        noi_dung="Nộp quỹ về công ty"
    ))

    # Ghi cộng quỹ công ty
    db.add(ThuChi(
        ngay=datetime.utcnow(),
        doi_tuong="cong_ty",
        ma_nv=user.ma_nv,
        so_tien=data.so_tien,
        loai="thu",
        hinh_thuc=data.hinh_thuc,
        noi_dung="Nhận tiền từ nhân viên"
    ))

    db.commit()

    return {"message": "Nộp quỹ thành công"}


# =====================================================
# BÁO CÁO TRONG NGÀY (NHÂN VIÊN)
# =====================================================
@router.get("/bao-cao-hom-nay")
def bao_cao_hom_nay(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    hom_nay = date.today()

    hoa_don_ban = db.query(HoaDonBan)\
        .filter(
            HoaDonBan.ma_nv == user.ma_nv,
            HoaDonBan.ngay == hom_nay
        ).all()

    hoa_don_nhap = db.query(HoaDonNhap)\
        .filter(
            HoaDonNhap.ma_nv == user.ma_nv,
            HoaDonNhap.ngay == hom_nay
        ).all()

    thu_chi = db.query(ThuChi)\
        .filter(
            ThuChi.ma_nv == user.ma_nv,
            func.date(ThuChi.ngay) == hom_nay
        ).all()

    # số dư quỹ nhân viên realtime
    tong = db.query(
        func.coalesce(
            func.sum(
                case(
                    (ThuChi.loai == "thu", ThuChi.so_tien),
                    else_=-ThuChi.so_tien
                )
            ), 0
        )
    ).filter(
        ThuChi.doi_tuong == "nhan_vien",
        ThuChi.ma_nv == user.ma_nv
    ).scalar()

    return {
        "hoa_don_ban_trong_ngay": hoa_don_ban,
        "hoa_don_nhap_trong_ngay": hoa_don_nhap,
        "thu_chi_trong_ngay": thu_chi,
        "so_du_quy_nhan_vien": Decimal(str(tong))
    }
    

def tinh_bao_cao_ngay(db: Session, ma_nv: str, ngay: date):

    tong_nhap = db.query(func.sum(Purchase.tong_tien)).filter(
        Purchase.ma_nv == ma_nv,
        Purchase.ngay == ngay
    ).scalar() or 0

    tong_ban = db.query(func.sum(Sale.tong_tien)).filter(
        Sale.ma_nv == ma_nv,
        Sale.ngay == ngay
    ).scalar() or 0

    tong_thu = db.query(func.sum(ThuChi.so_tien)).filter(
        ThuChi.ma_nv == ma_nv,
        ThuChi.loai == "thu",
        ThuChi.ngay == ngay
    ).scalar() or 0

    tong_chi = db.query(func.sum(ThuChi.so_tien)).filter(
        ThuChi.ma_nv == ma_nv,
        ThuChi.loai == "chi",
        ThuChi.ngay == ngay
    ).scalar() or 0

    return {
        "ma_nv": ma_nv,
        "ngay": ngay,
        "tong_nhap": tong_nhap,
        "tong_ban": tong_ban,
        "tong_thu": tong_thu,
        "tong_chi": tong_chi,
        "chenh_lech_tien_mat": tong_thu - tong_chi
    }

@router.get("/admin/bao-cao-ngay/{ma_nv}")
def admin_xem_bao_cao(
    ma_nv: str,
    ngay: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin được phép")

    return tinh_bao_cao_ngay(db, ma_nv, ngay)
   
@router.get("/bao-cao-ngay")
def bao_cao_ngay_nhan_vien(
    ngay: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "nhan_vien":
        raise HTTPException(status_code=403, detail="Không có quyền")

    return tinh_bao_cao_ngay(db, current_user.ma_nv, ngay)

@router.get("/admin/quy/{ma_nv}")
def admin_xem_quy_nhan_vien(
    ma_nv: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin được phép")

    return get_quy_nhan_vien(ma_nv, db)
