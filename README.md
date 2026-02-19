CTVT Core API

Core API phục vụ vận hành công ty gas CTVT.
Mục tiêu giai đoạn 1: xây dựng hệ thống nhập – bán – tồn kho tối giản, chạy ổn định.

🎯 Mục tiêu phiên bản 1 (Core)

Đăng nhập nhân viên

Nhập hàng (hóa đơn nhập)

Bán hàng (hóa đơn bán)

Quản lý tồn kho

Xem danh sách hóa đơn

Không bao gồm:

Chốt ngày

Thu chi nâng cao

VAT

Báo cáo kế toán

Snapshot tồn kho

🏗 Kiến trúc

Backend: FastAPI

Database: MySQL (Aiven)

ORM: SQLAlchemy

Deploy: Render

📦 Phạm vi API (Giai đoạn 1)
Authentication

POST /login

Purchase (Nhập hàng)

POST /purchase

GET /purchase

Sale (Bán hàng)

POST /sale

GET /sale

GET /sale/{id}

Inventory

GET /inventory

🧠 Nguyên tắc vận hành

Tất cả tạo hóa đơn phải nằm trong transaction.

Không thay đổi cấu trúc database hiện tại.

Không thêm tính năng ngoài phạm vi core.

Mỗi ngày chỉ hoàn thành 1 nhóm chức năng.

Mỗi thay đổi phải commit rõ ràng trên GitHub.

📅 Kế hoạch hoàn thành

Day 1:

Setup project

Kết nối database

Login

Day 2:

API nhập hàng

Day 3:

API bán hàng

Day 4:

API tồn kho

Day 5:

Test tổng thể + deploy

🚀 Trạng thái hiện tại

Đang triển khai phiên bản Core.

🔒 Lưu ý

Đây là hệ thống vận hành thực tế của công ty.
Ưu tiên:

Ổn định

Đơn giản

Không phức tạp hóa

Nâng cấp sẽ thực hiện sau khi hệ thống core chạy ổn định tối thiểu 2 tuần.

cây thư mục dự kiến làm:
ctvt-core-api/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── purchase.py
│   │   ├── sale.py
│   │   └── inventory.py
│   │
│   └── services.py
│
├── requirements.txt
├── README.md
└── DEV_STATUS.md

