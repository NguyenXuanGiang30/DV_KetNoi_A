# Đánh giá tiêu chí chấm điểm — A7: Notification Service

Bản tài liệu này tự đánh giá và đối chiếu dịch vụ **A7: Notification Service** với thang điểm và tiêu chí chấm điểm tích hợp hệ thống.

## Bảng tổng hợp kết quả

| Mã | Tiêu chí | Điểm tối đa | Trạng thái | Điểm tự đánh giá | Minh chứng & Vị trí trong dự án |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **A** | Nghiệp vụ rõ ràng | 1.0 | ✅ Đạt | 1.0 | Vai trò REST Provider. Định nghĩa API trong `contracts/notification.openapi.yaml` và mã nguồn `src/main.py`. |
| **B** | Chạy ổn định bằng Docker Compose | 1.5 | ✅ Đạt | 1.5 | Khai báo service `notification` trong `docker-compose.yml`, có cơ chế healthcheck. |
| **C** | Endpoint `/health` hoạt động | 1.0 | ✅ Đạt | 1.0 | API `GET /health` trả về HTTP 200 OK. |
| **D** | Tích hợp đúng contract với nhóm khác | 2.0 | ✅ Đạt | 2.0 | Tích hợp nhận sự kiện cảnh báo qua REST API đồng bộ từ Core Business thành công. |
| **E** | Payload / request đúng schema | 1.0 | ✅ Đạt | 1.0 | Sử dụng Pydantic models validate kiểu dữ liệu request đầu vào khớp 100% tài liệu OpenAPI. |
| **F** | Có xử lý lỗi / timeout | 1.0 | ✅ Đạt | 1.0 | Xác thực token bảo mật, xử lý ngoại lệ đầu vào, phản hồi cấu hình lỗi chuẩn Problem Details. |
| **G** | Minh chứng đầy đủ | 1.5 | ✅ Đạt | 1.5 | Đầy đủ hình ảnh và log tại thư mục `reports/`. |
| **H** | Trình bày demo rõ ràng | 1.0 | ✅ Đạt | 1.0 | Sử dụng kịch bản test tích hợp của `test_integration.py` làm demo luồng dữ liệu. |
| | **TỔNG CỘNG** | **10.0** | | **10.0/10.0** | |

---

## Chi tiết thực hiện theo từng tiêu chí

### Tiêu chí A: Nghiệp vụ rõ ràng (1.0đ)
- **Vai trò:** Cung cấp dịch vụ phát thông báo đa kênh (SMS, Telegram, Email, Console Log). Nhận yêu cầu gửi cảnh báo từ Core Business, xác thực, định tuyến và lưu vết lịch sử thông báo phục vụ tra cứu.
- **Input (Đầu vào):** REST API `POST /api/v1/notifications` chứa thông tin loại cảnh báo, mức độ nghiêm trọng, thông điệp cần gửi và danh sách kênh nhận (`channels`).
- **Xử lý (Logic chính):**
  * Kiểm tra token xác thực.
  * Phân tích và validate schema đầu vào bằng mô hình Pydantic.
  * Mô phỏng định tuyến gửi thông báo qua các kênh đã đăng ký (Telegram, SMS, Email, Console). Ghi nhật ký console mô phỏng thực tế.
  * Lưu trữ lịch sử thông báo vào bộ nhớ tạm thời (`notifications_db`).
- **Output (Đầu ra):** Trả về HTTP 201 Created cùng ID thông báo, trạng thái gửi, danh sách kênh đã truyền và thời gian gửi.
- **Tài liệu tham chiếu:**
  * OpenAPI Spec: `services/notification/contracts/notification.openapi.yaml`

### Tiêu chí B: Service chạy ổn định bằng Docker Compose (1.5đ)
- Dịch vụ được định nghĩa dưới tên service `notification` trong file `docker-compose.yml`.
- Chạy độc lập, không phụ thuộc vào các dịch vụ khác, đảm bảo luôn sẵn sàng tiếp nhận các thông báo khẩn cấp từ Core.
- Có cấu hình `healthcheck` tự động kiểm tra định kỳ 30 giây để giám sát trạng thái hoạt động.

### Tiêu chí C: Endpoint `/health` hoạt động (1.0đ)
- Endpoint triển khai tại: `GET /health` (Port `8007` ánh xạ vào container port `8000`).
- Phản hồi mẫu (HTTP 200 OK):
  ```json
  {
    "status": "ok",
    "service": "notification",
    "version": "1.0.0",
    "time": "2026-06-17T02:30:10Z"
  }
  ```
- Minh chứng đã được chụp ảnh lưu tại `reports/health-local.png`.

### Tiêu chí D: Tích hợp đúng contract với nhóm khác (2.0đ)
- Tích hợp thành công:
  * **REST Provider:** Cung cấp API nhận tin thông báo đồng bộ từ Core Business: `Core Business (A6)` $\xrightarrow{\text{POST /api/v1/notifications}}$ `Notification (A7)`.
- Quá trình liên kết tích hợp đã được chạy kiểm tra tự động qua file `test_integration.py`.

### Tiêu chí E: Payload / request đúng schema (1.0đ)
- Sử dụng thư viện Pydantic định nghĩa schema `NotificationRequest` và `NotificationResponse`.
- Validate định dạng dữ liệu đầu vào nghiêm ngặt. Nếu client gửi sai dữ liệu (ví dụ: thiếu thông điệp `message` hoặc rỗng), API sẽ trả về lỗi HTTP 422 Unprocessable Entity kèm mô tả chi tiết lỗi field tương ứng.

### Tiêu chí F: Có xử lý lỗi / timeout (1.0đ)
- **Cơ chế xác thực:** Tất cả các endpoint gửi thông báo đều được bảo vệ bằng Token Xác Thực Bearer. Nếu thiếu hoặc sai token, API sẽ phản hồi lỗi HTTP 401 Unauthorized theo chuẩn cấu trúc dữ liệu lỗi Problem Details (RFC 7807) chứ không gây crash.
- **Tránh tràn bộ nhớ:** Lịch sử thông báo lưu trữ tạm thời được giới hạn kích thước tối đa 1000 bản ghi gần nhất để tránh rò rỉ bộ nhớ (memory leaks).

### Tiêu chí G: Minh chứng đầy đủ (1.5đ)
- Các minh chứng đã chuẩn bị trong thư mục `reports/` gồm:
  * Danh sách container chạy ổn định: `reports/docker-compose-ps.png`
  * Nhật ký log thực tế: `reports/logs-compose.txt`
  * Sẵn sàng tích hợp: `reports/readiness-checklist.md`

### Tiêu chí H: Trình bày demo rõ ràng (1.0đ)
- **Luồng dữ liệu của service:**
  `POST /api/v1/notifications` $\rightarrow$ **[Xác thực & Ghi log gửi đa kênh]** $\rightarrow$ `HTTP REST Response (notification_id & status)`
- Quá trình chạy thử demo được tự động hóa tại mục `2.4` trong script kiểm thử tích hợp `test_integration.py`.
