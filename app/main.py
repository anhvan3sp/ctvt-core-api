from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

app = FastAPI()


@app.get("/")
def root():
    return {"message": "CTVT Core API running"}


@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        return {"db_status": "connected", "result": result[0]}
    except Exception as e:
        return {"db_status": "error", "detail": str(e)}
