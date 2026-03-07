from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from database import get_db
from models import Sale, SaleItem, Customer

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/day")
def report_day(ngay: date, db: Session = Depends(get_db)):

    rows = (
        db.query(
            Customer.ten_cua_hang.label("ten_kh"),
            SaleItem.so_luong,
            SaleItem.don_gia,
            (SaleItem.so_luong * SaleItem.don_gia).label("tong_tien"),
            Sale.tien_mat,
            Sale.tien_ck
        )
        .join(Sale, SaleItem.sale_id == Sale.id)
        .join(Customer, Sale.ma_kh == Customer.ma_kh)
        .filter(Sale.ngay == ngay)
        .all()
    )

    data = []

    tong_tien = 0
    tong_tien_mat = 0
    tong_chuyen_khoan = 0
    tong_so_binh = 0

    for r in rows:

        data.append({
            "ten_kh": r.ten_kh,
            "so_luong": r.so_luong,
            "don_gia": r.don_gia,
            "tong_tien": r.tong_tien,
            "tien_mat": r.tien_mat,
            "tien_ck": r.tien_ck
        })

        tong_tien += r.tong_tien
        tong_tien_mat += r.tien_mat
        tong_chuyen_khoan += r.tien_ck
        tong_so_binh += r.so_luong


    return {
        "data": data,
        "tong_tien": tong_tien,
        "tong_tien_mat": tong_tien_mat,
        "tong_chuyen_khoan": tong_chuyen_khoan,
        "tong_so_binh": tong_so_binh
    }
