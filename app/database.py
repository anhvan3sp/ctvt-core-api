import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

# Render sẽ tự cung cấp DATABASE_URL trong Environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL chưa được cấu hình")

# Tạo engine kết nối MySQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # tránh lỗi mất kết nối
    pool_recycle=3600,       # tái sử dụng connection
    echo=False               # True nếu muốn debug SQL
)

# Tạo session cho mỗi request
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base để các model kế thừa
Base = declarative_base()


# Dependency để dùng trong FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Hàm test kết nối (có thể gọi khi startup)
def test_connection():
    try:
        with engine.connect() as connection:
            print("✅ Kết nối database thành công")
    except OperationalError as e:
        print("❌ Không kết nối được database")
        raise e
