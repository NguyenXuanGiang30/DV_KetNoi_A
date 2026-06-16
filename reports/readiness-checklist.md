# READINESS CHECKLIST — BUỔI 6 (SMART CAMPUS PLATFORM)

Dưới đây là danh sách kiểm tra mức độ sẵn sàng tích hợp của toàn bộ 7 dịch vụ (Product) chạy trên cùng một máy demo giả lập.

## 1. Môi trường & Hạ tầng mạng
- [x] Máy demo đã kết nối đúng Wi-Fi hotspot demo.
- [x] Đã cấu hình và công bố danh sách cổng (port 8001 -> 8007) cho từng dịch vụ.
- [x] Đã cập nhật file `.env` với URL của các nhóm đối tác trỏ về nội bộ Docker Network (`http://<service-name>:8000`) và mở rộng cấu hình cho phép tích hợp LAN.
- [x] Các cổng được mở (publish port) ra ngoài máy Host thành công để các máy khác có thể kết nối thử:
  - **A1 (IoT Ingestion):** `8001`
  - **A2 (Camera Stream):** `8002`
  - **A3 (Access Gate):** `8003`
  - **A4 (AI Vision):** `8004`
  - **A5 (Analytics):** `8005`
  - **A6 (Core Business):** `8006`
  - **A7 (Notification):** `8007`

## 2. Docker & Trạng thái dịch vụ
- [x] Lệnh `docker compose ps` hiển thị toàn bộ 7 container đang ở trạng thái **healthy**.
- [x] Endpoint `GET /health` của toàn bộ 7 dịch vụ phản hồi thành công (HTTP 200 OK).
- [x] File `.env` chứa đầy đủ cấu hình kết nối HiveMQ Cloud (Host, Port, User, Password).
- [x] Kiểm tra log container xác nhận các dịch vụ subscribe và kết nối thành công đến MQTT broker.

## 3. Tích hợp dữ liệu và Quy tắc nghiệp vụ (Business Logic)
- [x] **IoT Ingestion (A1):** Đã load thành công tệp danh sách thiết bị mẫu (`IoT_device_registry.csv`) thông qua volume mount và xử lý phân loại chuẩn hóa dữ liệu thành công.
- [x] **Access Gate (A3):** Đã load thành công whitelist thẻ sinh viên mẫu (`Acessgate_uid_whitelist.csv`) qua volume mount và thực hiện kiểm tra quyền quẹt thẻ thành công.
- [x] **Camera Stream (A2) & AI Vision (A4):** Tích hợp phát hiện chuyển động và gọi dịch vụ AI nhận diện khuôn mặt thành công.
- [x] **Core Business (A6):** Nhận được các sự kiện chuẩn hóa từ các hàng đợi MQTT, kiểm tra nghiệp vụ và phát hiện vi phạm/bất thường thành công.
- [x] **Notification (A7):** Nhận sự kiện cảnh báo từ Core Business và giả lập gửi thông báo thành công qua Console/Telegram.
- [x] **Analytics (A5):** Thu thập dữ liệu thống kê từ toàn bộ hệ thống qua MQTT thành công.

## 4. Xử lý lỗi & Ngoại lệ
- [x] Đã có cơ chế giới hạn thời gian chờ (Timeout 3 - 5 giây) khi các dịch vụ gọi REST API của nhau.
- [x] Có cơ chế bắt lỗi và thông báo trạng thái lỗi rõ ràng (ví dụ: lỗi kết nối không làm treo hệ thống).
- [x] Các dịch vụ MQTT tự động kết nối lại khi mất mạng.

## 5. Minh chứng chuẩn bị
- [x] Đã sinh file `logs-compose.txt` lưu toàn bộ log chạy hệ thống.
- [x] Đã chụp ảnh danh sách container đang chạy và phản hồi `/health`.
- [x] Bộ tài liệu hợp đồng sự kiện và API OpenAPI đã được tích hợp đầy đủ trong thư mục của từng dịch vụ.
