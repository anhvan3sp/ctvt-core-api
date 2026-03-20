from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
import io

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
# 1. EXPORT TEMPLATE (FILE MẪU)
# ====================================================

@router.get("/export-dau-ky-template")
def export_template(user=Depends(get_current_user)):
    if user.vai_tro != "admin":
        raise HTTPException(403, "Chỉ admin")

    output = io.BytesIO()

    wb = Workbook()

    ws = wb.active
    ws.title = "ton_kho"
    ws.append(["ma_kho", "ma_sp", "so_luong"])

    ws = wb.create_sheet("quy_nhan_vien")
    ws.append(["ma_nv", "so_du"])

    ws = wb.create_sheet("quy_cong_ty")
    ws.append(["tien_mat", "tien_ngan_hang"])

    wb.save(output)

    # 🔥 QUAN TRỌNG
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=template_dau_ky.xlsx"
        }
    )
# ====================================================
# 2. VALIDATE
# ====================================================

def validate_excel(wb):
    errors = []

    required_sheets = ["ton_kho", "quy_nhan_vien", "quy_cong_ty"]

    for s in required_sheets:
        if s not in wb.sheetnames:
            errors.append(f"Thiếu sheet: {s}")

    if errors:
        return errors

    # ===== validate tồn kho =====
    ws = wb["ton_kho"]
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        ma_kho, ma_sp, so_luong = row

        if not ma_sp:
            errors.append(f"ton_kho dòng {i+2}: thiếu mã sản phẩm")

        if so_luong is not None and so_luong < 0:
            errors.append(f"ton_kho dòng {i+2}: số lượng âm")

    # ===== validate quỹ NV =====
    ws = wb["quy_nhan_vien"]
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        ma_nv, so_du = row

        if not ma_nv:
            errors.append(f"quy_nhan_vien dòng {i+2}: thiếu mã NV")

    return errors

# ====================================================
# 3. IMPORT (RESET / UPSERT)
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
        raise HTTPException(400, "mode phải là reset | upsert")

    try:
        wb = load_workbook(file.file)

        # ===== VALIDATE =====
        errors = validate_excel(wb)
        if errors:
            return {"status": "error", "errors": errors}

        with db.begin():

            # ❌ chặn nếu đã có giao dịch
            if db.query(ThuChi).count() > 0:
                raise HTTPException(400, "Đã có giao dịch, không cho import")

            # ===== RESET =====
            if mode == "reset":
                db.query(TonKhoChotNgay).delete()
                db.query(QuyNhanVienChotNgay).delete()
                db.query(QuyCongTyChotNgay).delete()

            # ===== TỒN KHO =====
            ws = wb["ton_kho"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                ma_kho, ma_sp, so_luong = row

                if not ma_sp:
                    continue

                db.execute("""
                    INSERT INTO ton_kho_chot_ngay (ma_kho, ma_sp, so_luong)
                    VALUES (:ma_kho, :ma_sp, :so_luong)
                    ON DUPLICATE KEY UPDATE so_luong = VALUES(so_luong)
                """, {
                    "ma_kho": ma_kho,
                    "ma_sp": ma_sp,
                    "so_luong": so_luong or 0
                })

            # ===== QUỸ NV =====
            ws = wb["quy_nhan_vien"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                ma_nv, so_du = row

                if not ma_nv:
                    continue

                db.execute("""
                    INSERT INTO quy_nhan_vien_chot_ngay (ma_nv, so_du)
                    VALUES (:ma_nv, :so_du)
                    ON DUPLICATE KEY UPDATE so_du = VALUES(so_du)
                """, {
                    "ma_nv": ma_nv,
                    "so_du": so_du or 0
                })

            # ===== QUỸ CTY =====
            ws = wb["quy_cong_ty"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                tien_mat, tien_ngan_hang = row

                tong = (tien_mat or 0) + (tien_ngan_hang or 0)

                db.query(QuyCongTyChotNgay).delete()

                db.add(QuyCongTyChotNgay(
                    tien_mat=tien_mat or 0,
                    tien_ngan_hang=tien_ngan_hang or 0,
                    tong_quy=tong
                ))

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(400, str(e))
