from fastapi import APIRouter, Depends
from datetime import date
from sqlalchemy.orm import Session
from db import get_db
from services.gas_du_service import chot_ngay_gas_du

router = APIRouter(prefix="/gas-du", tags=["gas-du"])


@router.post("/chot-ngay")
def chot_ngay(ngay: date, db: Session = Depends(get_db)):
    chot_ngay_gas_du(db, ngay)
    db.commit()
    return {"message": "Đã chốt ngày"}
