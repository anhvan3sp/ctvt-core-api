from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.routers import auth, purchase, sale, stock, finance
from app.auth_utils import get_password_hash
from fastapi.middleware.cors import CORSMiddleware
from app.routers import supplier, warehouse, product, report
from app.routers import customer
from app.routers import inventory


app = FastAPI()

# ==============================
# CORS CONFIG (mở full để test)
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # mở hết để tránh lỗi CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(inventory.router)
app.include_router(report.router)
app.include_router(customer.router)
app.include_router(supplier.router)
app.include_router(warehouse.router)
app.include_router(product.router)
# ==============================
# REGISTER ROUTERS
# ==============================
app.include_router(auth.router)
app.include_router(purchase.router)
app.include_router(sale.router)
app.include_router(stock.router)
app.include_router(finance.router)

# ==============================
# ROOT
# ==============================
@app.get("/")
def root():
    return {"message": "CTVT Core API running"}

# ==============================
# TEST DB
# ==============================
@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        return {"db_status": "connected", "result": result[0]}
    except Exception as e:
        return {"db_status": "error", "detail": str(e)}

# ==============================
# TEST HASH
# ==============================
@app.get("/create-hash")
def create_hash():
    return {"hash": get_password_hash("123abc")}
