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
NHẬT KÝ API – CTVT CORE

📅 Ngày: 22-02-2026

🎯 Mục tiêu hôm nay

Hoàn tất Authentication và chuẩn bị triển khai Purchase API.

✅ ĐÃ HOÀN THÀNH
1️⃣ Deploy & Environment

API chạy ổn định trên Render

Kết nối MySQL Aiven thành công

SSL & IP Access đã xử lý

JWT hoạt động bình thường

2️⃣ Authentication

Model NhanVien đã kết nối DB thật

Hash bcrypt lưu đúng format (60 ký tự)

Login trả về access_token thành công

Token decode lấy được ma_nv

Ví dụ log:

POST /auth/login → 200 OK

👉 Authentication hoàn tất.

3️⃣ Phân tích Purchase

Đã rà soát database hiện tại:

hoa_don_nhap

hoa_don_nhap_chi_tiet

nhat_ky_kho

Quyết định:

Không tạo bảng mới

Sử dụng cấu trúc DB hiện có

Ghi tồn kho qua nhat_ky_kho

⏸ CHƯA LÀM

Chưa viết services.py hoàn chỉnh cho Purchase

Chưa tạo router /purchase

Chưa test transaction

Chưa kiểm tra rollback

🧠 Trạng thái hệ thống hiện tại
Thành phần	Trạng thái
Deploy	✅ Ổn định
Database	✅ Kết nối OK
Authentication	✅ Hoàn thành
Purchase API	⏳ Chưa triển khai
📌 Vấn đề đã giải quyết hôm nay

Lỗi bcrypt Python 3.14 (backend detection)

Lỗi 72 bytes

Xác minh hash DB

Xác nhận login hoạt động

🚀 Kế hoạch ngày mai (Day 2 chính thức)

Viết create_hoa_don_nhap() trong services.py

Thêm ghi nhat_ky_kho trong transaction

Tạo router /purchase

Test tạo hóa đơn bằng Postman

Kiểm tra rollback nếu lỗi

🔒 Nhận định

Phần khó nhất (deploy + auth + DB thật) đã xong.
Từ mai trở đi chỉ là nghiệp vụ thuần.

Hệ thống core đang đi đúng hướng.
📒 NHẬT KÝ CTVT CORE API

Ngày: 23-02-2026
Giai đoạn: Day 2 – Purchase API

🎯 Mục tiêu hôm nay

Hoàn thiện xác thực token cho các API protected

Tạo router /purchase

Test POST hóa đơn nhập đầu tiên

✅ ĐÃ HOÀN THÀNH
1️⃣ Hoàn thiện cơ chế JWT

Bỏ OAuth2PasswordBearer

Chuyển sang dùng Header thủ công:

authorization: str = Header(...)

Token hoạt động đúng

/auth/login trả access_token chuẩn

2️⃣ Tạo router /purchase

Tạo file app/routers/purchase.py

Include router trong main.py

Swagger hiển thị:

POST /purchase

GET /purchase

3️⃣ Hoàn thiện service create_hoa_don_nhap

Hàm thực hiện:

Tạo hoa_don_nhap

Tạo hoa_don_nhap_chi_tiet

Ghi nhat_ky_kho

Tính tong_tien

Tất cả nằm trong transaction

Kiến trúc đúng hướng Core.

⚠ VẤN ĐỀ GẶP HÔM NAY
1️⃣ 422 – Thiếu header authorization

Lý do:

API yêu cầu Header

Swagger chưa nhập đúng chỗ

Đã xác định nguyên nhân.

2️⃣ 422 – Validation body

Có thể do:

Sai mã ma_ncc / ma_kho / ma_sp

Hoặc sai schema

Chưa test thành công hóa đơn đầu tiên.

📌 TRẠNG THÁI HỆ THỐNG

Auth: ✅ Ổn định

Router purchase: ✅ Load được

Header token: ✅ Nhận được

Purchase: ⏳ Chưa test thành công

DB: ✅ Kết nối ổn

🎯 KẾ HOẠCH NGÀY MAI

Test lại POST /purchase với:

Token đúng format

Mã tồn tại trong DB

Kiểm tra:

hoa_don_nhap

hoa_don_nhap_chi_tiet

nhat_ky_kho

Nếu OK → chuyển sang:

GET /purchase

Sau đó bắt đầu tồn kho

🧠 Đánh giá hôm nay

Phần khó nhất (auth + deploy + DB) đã qua.

Hệ thống đã có cấu trúc rõ ràng.

Còn lại chỉ là test và tinh chỉnh.

Tiến độ đang đi đúng hướng.

Mai vào lại chat này, nói:

"Tiếp tục test purchase"

Ta xử lý dứt điểm.

Nghỉ đi. Hôm nay làm đủ rồi.

Ngày 24.2.2026

📘 NHẬT KÝ NGÀY HÔM NAY
1️⃣ Hoàn thiện logic bán hàng

✔ Tính tồn kho realtime bằng SUM() trong DB (tối ưu hơn query all).
✔ Chặn bán nếu tồn không đủ.
✔ Tự động trừ kho bằng NhatKyKho (xuat).
✔ Tính tong_tien, no_lai chuẩn Decimal.

2️⃣ Chuẩn hóa logic quỹ

Sửa lại toàn bộ mô hình tiền:

Quy tắc mới:

Nhân viên đặc biệt:

Tiền mặt → vào quỹ nhân viên

Chuyển khoản → vào ngân hàng công ty

Admin:

Tiền mặt → vào quỹ công ty

Chuyển khoản → vào ngân hàng công ty

✔ Thêm:

/finance/quy-cong-ty

/finance/nop-quy

/finance/close-day

3️⃣ Bắt đầu xây báo cáo công nợ

✔ API:

/finance/cong-no/{ma_kh}

/finance/cong-no

Logic:

Tổng bán

Tổng đã thu

Tổng còn nợ

4️⃣ Lỗi cuối ngày

Server die vì:

NameError: name 'Header' is not defined

Nguyên nhân:
Trong auth_utils.py có dùng:

authorization: str = Header(...)

nhưng thiếu:

from fastapi import Header

=> Lỗi rất nhỏ. Mai sửa 1 dòng là chạy lại.

📊 Trạng thái hệ thống hiện tại
Module	Trạng thái
Auth	OK
Purchase	OK
Sale	OK
Tồn kho realtime	OK
Quỹ nhân viên	OK
Quỹ công ty	OK
Công nợ	Đang hoàn thiện
Phân quyền role	Cơ bản xong
🧠 Điều quan trọng hôm nay

Hệ thống đã chuyển từ:

“API CRUD đơn giản”

sang

“Core ERP mini có logic tài chính thật”

Đây là bước chuyển rất lớn.

🎯 Ngày mai làm tiếp

Sửa lỗi Header

Hoàn thiện báo cáo công nợ chi tiết

Chặn bán nếu nợ vượt hạn mức

Hoàn thiện phân quyền theo role thực chiến
