from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HoaDonBanCreate
from app.services import create_hoa_don_ban
from app.auth_utils import require_roles

router = APIRouter(prefix="/sale", tags=["Sale"])


@router.post("/")
def create_sale(
    data: HoaDonBanCreate,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "nv_dac_biet"]))
):
    return create_hoa_don_ban(db, data, user.ma_nv)
