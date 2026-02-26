CTVT CORE API

Backend vận hành nội bộ cho công ty gas CTVT.
Hệ thống phục vụ nhập hàng – bán hàng – tồn kho – tài chính cơ bản.

Trạng thái hiện tại: Beta nội bộ – đang sử dụng thật

🎯 Mục tiêu hệ thống

Xây dựng một Core ERP mini với các tiêu chí:

Ổn định

Chính xác dữ liệu

Không âm kho

Có transaction đầy đủ

Không phụ thuộc thao tác thủ công

Không hướng tới phức tạp hóa giai đoạn đầu.

🏗 Kiến trúc hệ thống

Backend: FastAPI
Database: MySQL (Aiven Cloud)
ORM: SQLAlchemy
Authentication: JWT
Deploy: Render

Kiến trúc phân tầng:

Router → Service → Database

Nguyên tắc:

Router chỉ xử lý request và auth

Business logic nằm trong services.py

Mọi thao tác tạo hóa đơn đều nằm trong transaction

📂 Cấu trúc thư mục thực tế
ctvt-core-api/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth_utils.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── purchase.py
│   │   ├── sale.py
│   │   └── finance.py
│   │
│   └── services.py
│
├── requirements.txt
├── runtime.txt
├── README.md
└── DEV_STATUS.md

Lưu ý:

Không có file inventory.py riêng.

Tồn kho được tính realtime từ bảng nhat_ky_kho.

🔐 Authentication

Sử dụng JWT (JSON Web Token).

Login

POST /auth/login

Trả về:

{
  "access_token": "...",
  "token_type": "bearer"
}

Các API protected yêu cầu header:

Authorization: Bearer <access_token>

Token chứa:

ma_nv

vai_tro

📦 API Modules
1️⃣ Purchase – Nhập hàng

POST /purchase
GET /purchase

Khi tạo hóa đơn nhập:

Tạo hoa_don_nhap

Tạo hoa_don_nhap_chi_tiet

Ghi nhat_ky_kho (loai = nhap)

Toàn bộ nằm trong transaction.

Rollback nếu có lỗi.

2️⃣ Sale – Bán hàng

POST /sale
GET /sale
GET /sale/{id}

Logic:

Kiểm tra tồn kho realtime bằng SUM()

Không cho bán nếu tồn không đủ

Ghi nhat_ky_kho (loai = xuat)

Tính tong_tien bằng Decimal

Không lưu tồn snapshot.
Tồn kho tính động từ nhat_ky_kho.

3️⃣ Finance – Tài chính cơ bản

Bao gồm:

Quỹ công ty

Quỹ nhân viên đặc biệt

Báo cáo hôm nay

Công nợ khách hàng

Nộp quỹ

Close day

Hệ thống có trigger MySQL để:

Khóa UPDATE dữ liệu ngày cũ

Khóa DELETE dữ liệu ngày cũ

Dữ liệu tài chính không thể sửa sau khi qua ngày.

📊 Cách tính tồn kho

Tồn kho không lưu trực tiếp.

Công thức:

SUM(nhap) - SUM(xuat)

Nguồn dữ liệu: bảng nhat_ky_kho.

Ưu điểm:

Không sai lệch tồn

Không cần đồng bộ snapshot

Không lệ thuộc cache

🧠 Nguyên tắc kỹ thuật

Mọi hóa đơn phải nằm trong transaction.

Không cho âm kho.

Không đặt business logic trong router.

Không sửa dữ liệu ngày cũ.

Không thêm tính năng ngoài phạm vi cần thiết.

Ưu tiên chính xác hơn tối ưu sớm.

⚙️ Thiết lập môi trường

Yêu cầu:

Python 3.11 (bắt buộc do tương thích bcrypt)

Cài thư viện:

pip install -r requirements.txt

Chạy local:

uvicorn app.main:app --reload

Production (Render):

uvicorn app.main:app --host 0.0.0.0 --port 10000
📌 Trạng thái hệ thống hiện tại
Module	Trạng thái
Deploy	Ổn định
Database	Kết nối OK
Authentication	Hoàn tất
Purchase	Hoạt động
Sale	Hoạt động
Finance	Gần hoàn chỉnh
Transaction	Ổn định
Rollback	Hoạt động

Độ ổn định ước tính: ~85–90% (Beta nội bộ)

🚀 Định hướng tiếp theo

Giai đoạn tiếp theo:

Xây dựng frontend bằng React + Vite

Kết nối API thật

Hoàn thiện dashboard

Chuẩn hóa phân quyền nâng cao

Viết tài liệu API cho frontend

Không mở rộng backend thêm trước khi frontend ổn định.

🔒 Lưu ý

Đây là hệ thống vận hành nội bộ thật.

Ưu tiên:

Ổn định

Đơn giản

Không phức tạp hóa

Không refactor lớn khi chưa cần

Mọi nâng cấp lớn chỉ thực hiện khi hệ thống core chạy ổn định tối thiểu 2 tuần.
