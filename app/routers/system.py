@router.post("/khoi-tao-dau-ky")
def khoi_tao_dau_ky(
    data: KhoiTaoDauKyRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    if user.vai_tro != "admin":
        raise HTTPException(403, "Chỉ admin được khởi tạo")

    try:
        with db.begin():

            # =========================
            # 0. CHECK ĐÃ KHỞI TẠO CHƯA
            # =========================
            da_co = db.query(QuyCongTyChotNgay).first()
            if da_co:
                raise HTTPException(400, "Đã khởi tạo rồi, không chạy lại")

            # =========================
            # 1. TỒN KHO (CURRENT)
            # =========================
            for item in data.ton_kho:

                db.add(TonKhoChotNgay(
                    ma_sp=item.ma_sp,
                    ma_kho=item.ma_kho,
                    so_luong=item.so_luong
                ))

            # =========================
            # 2. QUỸ NHÂN VIÊN (CURRENT)
            # =========================
            for q in data.quy_nhan_vien:

                db.add(QuyNhanVienChotNgay(
                    ma_nv=q.ma_nv,
                    so_du=q.so_du
                ))

            # =========================
            # 3. QUỸ CÔNG TY (CURRENT)
            # =========================
            db.add(QuyCongTyChotNgay(
                tien_mat=data.quy_cong_ty,
                tien_ngan_hang=0,
                tong_quy=data.quy_cong_ty
            ))

        return {
            "message": "Khởi tạo OK"
        }

    except Exception as e:
        raise HTTPException(500, str(e))
