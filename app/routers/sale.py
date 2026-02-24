router = APIRouter(prefix="/sale", tags=["Sale"])

@router.post("/")
def create_sale(
    data: HoaDonBanCreate,
    db: Session = Depends(get_db),
    ma_nv: str = Depends(get_current_user)
):
    return create_hoa_don_ban(db, data, ma_nv)
