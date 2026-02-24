from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.routers import auth, purchase, sale
from app.auth_utils import get_password_hash
from app.routers import stock


app = FastAPI()

# ==============================
# REGISTER ROUTERS
# ==============================
app.include_router(auth.router)
app.include_router(purchase.router)
app.include_router(sale.router)
app.include_router(stock.router)

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
