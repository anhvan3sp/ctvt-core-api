from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from openpyxl import Workbook, load_workbook
import os
import tempfile

from app.database import get_db
from app.auth_utils import get_current_user
from app.models import (
    TonKhoChotNgay,
    QuyNhanVienChotNgay,
    QuyCongTyChotNgay,
    ThuChi
)

router = APIRouter(prefix="/system", tags=["system"])

# ====================================================
# EXPORT TEMPLATE (100% KHÔNG LỖI)
# ====================================================

@router.get("/export-dau-ky-template")
def export_template(user=Depends(get_current_user)):
    if user.vai_tro != "admin":
        raise HTTPException(403, "Chỉ admin")

    # 👉 tạo file thật
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    file_path = tmp.name

    wb = Workbook()

    ws = wb.active
    ws.title = "ton_kho"
    ws.append(["ma_kho", "ma_sp", "so_luong"])

    ws = wb.create_sheet("quy_nhan_vien")
    ws.append(["ma_nv", "so_du"])

    ws = wb.create_sheet("quy_cong_ty")
    ws.append(["tien_mat", "tien_ngan_hang"])

    wb.save(file_path)
    wb.close()

    return FileResponse(
        path=file_path,
        filename="template_dau_ky.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ====================================================
# VALIDATE
# ====================================================

def validate_excel(wb):
    errors = []

    required = ["ton_kho", "quy_nhan_vien", "quy_cong_ty"]

    for s in required:
        if s not in wb.sheetnames:
            errors.append(f"Thiếu sheet: {s}")

    if errors:
        return errors

    ws = wb["ton_kho"]
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        ma_kho, ma_sp, so_luong = row

        if not ma_sp:
            errors.append(f"ton_kho dòng {i+2}: thiếu mã SP")

        if so_luong is not None and so_luong < 0:
            errors.append(f"ton_kho dòng {i+2}: số lượng âm")

    ws = wb["quy_nhan_vien"]
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        ma_nv, _ = row

        if not ma_nv:
            errors.append(f"quy_nhan_vien dòng {i+2}: thiếu mã NV")

    return errors

# ====================================================
# IMPORT
# ====================================================

@router.post("/import-dau-ky")
def import_dau_ky(
    mode: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    if user.vai_tro != "admin":
        raise HTTPException(403, "Chỉ admin")

    if mode not in ["reset", "upsert"]:
        raise HTTPException(400, "mode sai")

    wb = load_workbook(file.file)

    errors = validate_excel(wb)
    if errors:
        return {"status": "error", "errors": errors}

    with db.begin():

        if db.query(ThuChi).count() > 0:
            raise HTTPException(400, "Đã có giao dịch")

        if mode == "reset":
            db.query(TonKhoChotNgay).delete()
            db.query(QuyNhanVienChotNgay).delete()
            db.query(QuyCongTyChotNgay).delete()

        # TON KHO
        data = []
        ws = wb["ton_kho"]

        for row in ws.iter_rows(min_row=2, values_only=True):
            ma_kho, ma_sp, so_luong = row
            if not ma_sp:
                continue

            data.append({
                "ma_kho": ma_kho,
                "ma_sp": ma_sp,
                "so_luong": so_luong or 0
            })

        if data:
            db.execute("""
                INSERT INTO ton_kho_chot_ngay (ma_kho, ma_sp, so_luong)
                VALUES (:ma_kho, :ma_sp, :so_luong)
                ON DUPLICATE KEY UPDATE so_luong = VALUES(so_luong)
            """, data)

        # QUỸ NV
        data = []
        ws = wb["quy_nhan_vien"]

        for row in ws.iter_rows(min_row=2, values_only=True):
            ma_nv, so_du = row
            if not ma_nv:
                continue

            data.append({
                "ma_nv": ma_nv,
                "so_du": so_du or 0
            })

        if data:
            db.execute("""
                INSERT INTO quy_nhan_vien_chot_ngay (ma_nv, so_du)
                VALUES (:ma_nv, :so_du)
                ON DUPLICATE KEY UPDATE so_du = VALUES(so_du)
            """, data)

        # QUỸ CTY
        ws = wb["quy_cong_ty"]
        db.query(QuyCongTyChotNgay).delete()

        for row in ws.iter_rows(min_row=2, values_only=True):
            tien_mat, tien_ngan_hang = row
            tong = (tien_mat or 0) + (tien_ngan_hang or 0)

            db.add(QuyCongTyChotNgay(
                tien_mat=tien_mat or 0,
                tien_ngan_hang=tien_ngan_hang or 0,
                tong_quy=tong
            ))

    return {"status": "success"}
