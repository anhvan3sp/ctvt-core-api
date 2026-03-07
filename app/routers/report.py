from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import Sale, Purchase, ThuChi, Customer, SaleItem

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/day")
def report_day(ngay: date, db: Session = Depends(get_db)):

    # ===== BÁN HÀNG =====

    sales = (
        db.query(Sale, Customer.ten_cua_hang)
        .join(Customer, Sale.ma_kh == Customer.ma_kh)
        .filter(Sale.ngay == ngay)
        .all()
    )

    hoa_don_ban = []

    tong_ban = 0
    tong_tien_mat = 0
    tong_tien_ck = 0
    tong_so_binh_ban = 0

    for s, ten_kh in sales:

        # tính số bình trong hóa đơn
        items = db.query(SaleItem).filter(SaleItem.sale_id == s.id).all()

        so_binh = sum(i.so_luong for i in items)

        tong_so_binh_ban += so_binh

        hoa_don_ban.append({
            "so_hd": s.so_hd,
            "ten_kh": ten_kh,
            "so_binh": so_binh,
            "tong_tien": s.tong_tien,
            "tien_mat": s.tien_mat,
            "tien_ck": s.tien_ck,
            "tong_thanh_toan": s.tong_thanh_toan,
            "ngay": s.ngay
        })

        tong_ban += s.tong_thanh_toan
        tong_tien_mat += s.tien_mat
        tong_tien_ck += s.tien_ck


    # ===== NHẬP HÀNG =====

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


    # ===== THU CHI =====

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

            "tong_so_binh_ban": tong_so_binh_ban,

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
