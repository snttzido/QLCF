# Website Quản Lý Quán Cà Phê

Toàn bộ backend viết bằng **Python** (Flask + sqlite3 chuẩn thư viện), giao diện dùng **Bootstrap 5** (qua CDN, chỉ là thư viện CSS/JS, không viết thêm code JS phức tạp).

## Cài đặt & chạy

```bash
cd cafe_app
pip install -r requirements.txt
python app.py
```

Mở trình duyệt tại: http://127.0.0.1:5000

Cơ sở dữ liệu SQLite (`cafe.db`) sẽ tự động được tạo với dữ liệu mẫu (10 món, 6 bàn) trong lần chạy đầu tiên.

## Cấu trúc thư mục

```
cafe_app/
├── app.py            # Toàn bộ route Flask (khách hàng + nhân viên)
├── database.py        # Hàm kết nối & truy vấn SQLite
├── schema.sql          # Cấu trúc bảng + dữ liệu mẫu
├── requirements.txt
├── templates/
│   ├── base.html       # Layout chung, navbar Bootstrap
│   ├── customer/        # Giao diện khách hàng
│   │   ├── menu.html
│   │   ├── cart.html
│   │   └── order_success.html
│   └── staff/            # Giao diện nhân viên
│       ├── menu_manage.html
│       ├── menu_form.html
│       ├── orders.html
│       ├── order_detail.html
│       ├── tables.html
│       └── payment.html
```

## Chức năng

### Phía khách hàng
- **Quét mã QR tại bàn**: mỗi bàn có một mã QR riêng dẫn tới `/ban/<số_bàn>`. Quét mã sẽ tự động gán bàn đó cho phiên gọi món (hiện banner "Đang gọi món cho Bàn X" trên mọi trang).
- **Xem menu món**: `/menu` — danh sách đồ uống/đồ ăn, lọc theo loại, giá và mô tả.
- **Chọn món**: chọn số lượng và thêm vào giỏ hàng ngay trên trang menu.
- **Giỏ hàng**: `/cart` — xem, thay đổi số lượng, xóa món. Nếu vào từ QR, bàn được điền sẵn tự động.
- **Đặt món**: xác nhận đơn hàng → tạo đơn với trạng thái "Chờ xác nhận" → chuyển sang trang thanh toán.
- **Thanh toán**: `/order/<id>/payment` — chọn 1 trong 2 hình thức:
  - **Tiền mặt**: hiển thị thông báo thanh toán tại quầy.
  - **Chuyển khoản**: hiển thị mã QR chuyển khoản (kèm số tiền, nội dung chuyển khoản) để khách quét bằng app ngân hàng.

### Phía nhân viên
- **Quản lý món**: `/staff/menu` — thêm, sửa, xóa, bật/tắt bán món.
- **Quản lý đơn**: `/staff/orders` — xem đơn khách đặt, lọc theo trạng thái, cập nhật trạng thái: Chờ xác nhận → Đang chuẩn bị → Đã hoàn thành / Đã hủy.
- **Quản lý bàn**: `/staff/tables` — theo dõi trạng thái Trống / Có khách, thêm/xóa bàn, **xem mã QR của từng bàn** và bấm "In QR" để in ra dán lên bàn.
- **Thanh toán**: `/staff/payment` — xem các đơn chưa thanh toán, hình thức khách đã chọn (Tiền mặt / Chuyển khoản), tính tổng tiền, xác nhận thanh toán (tự động giải phóng bàn về trạng thái Trống).

### Mã QR dán trên bàn
Vào **Quản lý bàn** (`/staff/tables`), mỗi bàn có QR nhỏ xem trước; bấm **"In QR"** để mở trang in khổ lớn (`/staff/tables/<id>/qr`), có nút in ngay trên trình duyệt. QR mã hoá đường link `http://<địa_chỉ_server>/ban/<id>` — khi triển khai thật, hãy chạy server ở một địa chỉ khách hàng truy cập được (domain/IP thật, không phải `127.0.0.1`) rồi mới in QR để khách quét được.

Thông tin ngân hàng dùng để tạo QR chuyển khoản được khai báo ở biến `BANK_INFO` đầu file `app.py` — hãy sửa lại theo thông tin quán thực tế trước khi dùng.

## Ghi chú
- Giỏ hàng của khách được lưu tạm trong `session` (phía server, không dùng localStorage).
- Toàn bộ mã nguồn là Python + HTML/Jinja2 + Bootstrap (CSS/JS thư viện), không dùng ngôn ngữ backend nào khác.
- Có thể đổi `app.secret_key` trong `app.py` trước khi triển khai thật.
