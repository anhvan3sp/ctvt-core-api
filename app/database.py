import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL chưa được cấu hình")

# ✅ Engine: thêm init_command để set timezone VN cho mỗi connection
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "ssl": {},
        "init_command": "SET time_zone = '+07:00'"
    }
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        # ✅ Đảm bảo mỗi session luôn chạy đúng timezone (double safety)
        db.execute(text("SET time_zone = '+07:00'"))
        yield db
    finally:
        db.close()
