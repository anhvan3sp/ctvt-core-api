from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from database import get_db
from models import Sale, SaleItem, Customer

router = APIRouter(prefix="/report", tags=["report"])

@router.get("/day")
def report_day(ngay: date, db: Session = Depends(get_db)):

    sales = db.query(Sale).filter(Sale.ngay == ngay).all()

    result = []

    tong_tien = 0
    tong_tien_mat = 0
    tong_chuyen_khoan = 0

    for s in sales:

        customer = db.query(Customer).filter(Customer.ma_kh == s.ma_kh).first()

        items = db.query(SaleItem).filter(SaleItem.sale_id == s.id).all()

        for item in items:

            row = {
                "ten_kh": customer.ten_cua_hang,
                "so_luong": item.so_luong,
                "don_gia": item.don_gia,
                "tong_tien": item.so_luong * item.don_gia,
                "da_tra": s.tien_mat + s.tien_ck
            }

            result.append(row)

        tong_tien += s.tong_tien
        tong_tien_mat += s.tien_mat
        tong_chuyen_khoan += s.tien_ck

    return {
        "data": result,
        "tong_tien": tong_tien,
        "tong_tien_mat": tong_tien_mat,
        "tong_chuyen_khoan": tong_chuyen_khoan
    }
