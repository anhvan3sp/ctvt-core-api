from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import KhachHang
from app.schemas import CustomerCreate, CustomerResponse
from sqlalchemy import func
from app.models import HoaDonBan
router = APIRouter(prefix="/customer", tags=["Customer"])


@router.post("/", response_model=CustomerResponse)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(KhachHang).filter(KhachHang.ma_kh == data.ma_kh).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mã khách hàng đã tồn tại")

    customer = KhachHang(**data.dict())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/", response_model=List[CustomerResponse])
def get_customers(db: Session = Depends(get_db)):
    return db.query(KhachHang).all()

@router.get("/debt/{ma_kh}")
def get_customer_debt(ma_kh: str, db: Session = Depends(get_db)):

    # ===== Kiểm tra khách =====
    kh = db.query(KhachHang).filter(KhachHang.ma_kh == ma_kh).first()
    if not kh:
        raise HTTPException(status_code=404, detail="Khách hàng không tồn tại")

    # ===== Tổng bán =====
    tong_ban = db.query(
        func.coalesce(func.sum(HoaDonBan.tong_tien), 0)
    ).filter(
        HoaDonBan.ma_kh == ma_kh
    ).scalar()

    # ===== Tổng đã trả =====
    tong_da_tra = db.query(
        func.coalesce(func.sum(HoaDonBan.tong_thanh_toan), 0)
    ).filter(
        HoaDonBan.ma_kh == ma_kh
    ).scalar()

    # ===== Tổng công nợ hiện tại =====
    tong_cong_no = db.query(
        func.coalesce(func.sum(HoaDonBan.no_lai), 0)
    ).filter(
        HoaDonBan.ma_kh == ma_kh
    ).scalar()

    # ===== Hóa đơn còn nợ =====
    hoa_don_con_no = db.query(HoaDonBan).filter(
        HoaDonBan.ma_kh == ma_kh,
        HoaDonBan.no_lai > 0
    ).all()

    ds_hoa_don = [
        {
            "id": hd.id,
            "ngay": hd.ngay,
            "tong_tien": float(hd.tong_tien),
            "da_tra": float(hd.tong_thanh_toan),
            "con_no": float(hd.no_lai)
        }
        for hd in hoa_don_con_no
    ]

    return {
        "ma_kh": ma_kh,
        "ten_khach": kh.ten_cua_hang,
        "tong_ban": float(tong_ban),
        "tong_da_tra": float(tong_da_tra),
        "tong_cong_no": float(tong_cong_no),
        "so_hoa_don_con_no": len(ds_hoa_don),
        "danh_sach_hoa_don_con_no": ds_hoa_don
    }
