from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HoaDonBanCreate
from app.services import create_hoa_don_ban
from app.auth_utils import get_current_user

router = APIRouter(prefix="/sale", tags=["Sale"])


@router.post("/")
def create_sale(
    data: HoaDonBanCreate,
    db: Session = Depends(get_db),
    ma_nv: str = Depends(get_current_user)
):
    return create_hoa_don_ban(db, data, ma_nv)
