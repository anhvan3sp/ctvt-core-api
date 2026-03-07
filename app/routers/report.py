from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import Sale, Purchase, ThuChi, Customer

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/day")
def report_day(ngay: date, db: Session = Depends(get_db)):

    sales = db.query(Sale).filter(Sale.ngay == ngay).all()

    hoa_don_ban = []

    tong_ban = 0
    tong_tien_mat = 0
    tong_tien_ck = 0

    for s in sales:

        kh = db.query(Customer).filter(Customer.ma_kh == s.ma_kh).first()

        hoa_don_ban.append({
            "so_hd": s.so_hd,
            "ten_kh": kh.ten_cua_hang if kh else s.ma_kh,
            "tong_tien": s.tong_tien,
            "tien_mat": s.tien_mat,
            "tien_ck": s.tien_ck,
            "ngay": s.ngay
        })

        tong_ban += s.tong_tien
        tong_tien_mat += s.tien_mat
        tong_tien_ck += s.tien_ck


    purchases = db.query(Purchase).filter(Purchase.ngay == ngay).all()

    hoa_don_nhap = []
    tong_nhap = 0

    for p in purchases:

        hoa_don_nhap.append({
            "so_hd": p.so_hd,
            "tong_tien": p.tong_tien,
            "ngay": p.ngay
        })

        tong_nhap += p.tong_tien


    thu_chi = db.query(ThuChi).filter(ThuChi.ngay == ngay).all()

    thu_chi_trong_ngay = []

    tong_thu = 0
    tong_chi = 0

    for t in thu_chi:

        thu_chi_trong_ngay.append({
            "doi_tuong": t.doi_tuong,
            "so_tien": t.so_tien,
            "hinh_thuc": t.hinh_thuc,
            "ngay": t.ngay
        })

        if t.so_tien > 0:
            tong_thu += t.so_tien
        else:
            tong_chi += abs(t.so_tien)


    return {

        "hoa_don_ban_trong_ngay": hoa_don_ban,

        "hoa_don_nhap_trong_ngay": hoa_don_nhap,

        "thu_chi_trong_ngay": thu_chi_trong_ngay,

        "tong_ket": {

            "tong_ban": tong_ban,

            "tong_nhap": tong_nhap,

            "tong_tien_mat": tong_tien_mat,

            "tong_chuyen_khoan": tong_tien_ck,

            "tong_thu_khac": tong_thu,

            "tong_chi": tong_chi,

            "ton_quy_cuoi_ngay":
                tong_tien_mat
                + tong_thu
                - tong_chi
                - tong_nhap
        }

    }
