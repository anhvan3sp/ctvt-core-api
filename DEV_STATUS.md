Nhật kí API ctvt-core-api
Ngày: 19-02-2026
🎯 Mục tiêu hôm nay

Deploy API lên Render và kết nối thành công với MySQL trên Aiven.

✅ ĐÃ HOÀN THÀNH
1. Deploy API lên Render

Tạo Web Service ctvt-core-api

Cấu hình:

Build: pip install -r requirements.txt

Start: uvicorn app.main:app --host 0.0.0.0 --port 10000

Service chạy thành công

Endpoint / hoạt động

2. Kết nối MySQL (Aiven)

Cấu hình DATABASE_URL đúng format

Cài thêm:

cryptography

Xử lý lỗi SSL

Xử lý lỗi IP Access

Tạo user DB riêng cho API

Endpoint /test-db trả về:

{
  "db_status": "connected",
  "result": 1
}


→ Database đã kết nối thành công.

3. Thiết lập Authentication

Tạo model NhanVien

Tạo schema LoginRequest, LoginResponse

Tạo auth_utils.py

verify_password

get_password_hash

create_access_token

Tạo router auth.py

Include router trong main.py

⚠ VẤN ĐỀ GẶP PHẢI
1. bcrypt lỗi trên Python 3.14

Render dùng Python 3.14 → passlib + bcrypt không tương thích.

Lỗi:

ValueError: password cannot be longer than 72 bytes


Kết luận:
Phải downgrade Python xuống 3.11.

⏳ VIỆC CẦN LÀM NGÀY MAI

Tạo file runtime.txt:

python-3.11.9


Redeploy sạch (Clear build cache)

Tạo hash password trực tiếp trên Render

Update password_hash cho user admin

Test endpoint:

POST /auth/login


Nếu login OK → chuyển sang làm Purchase API.

📌 Trạng thái hệ thống hiện tại

API: Running

DB: Connected

Login: Chưa hoàn tất do lỗi môi trường Python

Hôm nay đã vượt qua phần khó nhất: deploy + kết nối DB thật.

Mai chỉ còn xử lý môi trường Python và hoàn tất login.

Nghỉ ngơi đi sếp. Mai làm tiếp cho gọn.
