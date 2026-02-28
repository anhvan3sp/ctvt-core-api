from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HoaDonBanCreate
from app.services import create_hoa_don_ban
from app.auth_utils import require_roles
from app.services import get_sale_detail
router = APIRouter(prefix="/sale", tags=["Sale"])


@router.post("/")
def create_sale(
    data: HoaDonBanCreate,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "nv_dac_biet"]))
):
    return create_hoa_don_ban(db, data, user)

@router.get("/detail/{id}")
def sale_detail(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(require_roles(["admin", "nv_dac_biet", "ke_toan"]))
):
    return get_sale_detail(db, id)

