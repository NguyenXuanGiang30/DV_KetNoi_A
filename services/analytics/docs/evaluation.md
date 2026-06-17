# Đánh giá tiêu chí chấm điểm — A5: Analytics Service

Bản tài liệu này tự đánh giá và đối chiếu dịch vụ **A5: Analytics Service** với thang điểm và tiêu chí chấm điểm tích hợp hệ thống.

## Bảng tổng hợp kết quả

| Mã | Tiêu chí | Điểm tối đa | Trạng thái | Điểm tự đánh giá | Minh chứng & Vị trí trong dự án |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **A** | Nghiệp vụ rõ ràng | 1.0 | ✅ Đạt | 1.0 | Vai trò Consumer & REST Provider. Mô tả nghiệp vụ dưới đây, OpenAPI tại `contracts/analytics.openapi.yaml`. |
| **B** | Chạy ổn định bằng Docker Compose | 1.5 | ✅ Đạt | 1.5 | Khai báo service `analytics` trong `docker-compose.yml`, có cơ chế healthcheck. |
| **C** | Endpoint `/health` hoạt động | 1.0 | ✅ Đạt | 1.0 | API `GET /health` trả về HTTP 200 OK. |
| **D** | Tích hợp đúng contract với nhóm khác | 2.0 | ✅ Đạt | 2.0 | Tích hợp subscribe 4 topic MQTT từ 4 service nguồn và cung cấp REST API cho khách hàng. |
| **E** | Payload / request đúng schema | 1.0 | ✅ Đạt | 1.0 | Đọc và xử lý các MQTT event payload theo đúng các Event Contract đã cam kết. |
| **F** | Có xử lý lỗi / timeout | 1.0 | ✅ Đạt | 1.0 | Các phép tính toán an toàn, log lỗi rõ ràng khi parse payload hỏng, tự động reconnect MQTT. |
| **G** | Minh chứng đầy đủ | 1.5 | ✅ Đạt | 1.5 | Đầy đủ hình ảnh và log tại thư mục `reports/`. |
| **H** | Trình bày demo rõ ràng | 1.0 | ✅ Đạt | 1.0 | Sử dụng kịch bản test tích hợp của `test_integration.py` làm demo luồng dữ liệu. |
| | **TỔNG CỘNG** | **10.0** | | **10.0/10.0** | |

---

## Chi tiết thực hiện theo từng tiêu chí

### Tiêu chí A: Nghiệp vụ rõ ràng (1.0đ)
- **Vai trò:** Trung tâm tổng hợp dữ liệu (Data Aggregator). Đăng ký nhận toàn bộ các sự kiện từ các dịch vụ khác qua hàng đợi MQTT để tính toán và lưu trữ các chỉ số hoạt động then chốt (KPI) của toàn bộ khuôn viên, phục vụ hiển thị dashboard thời gian thực.
- **Input (Đầu vào):** Nhận sự kiện từ 4 topic MQTT:
  * `smart-campus/events/sensor`: Sự kiện môi trường đã chuẩn hóa từ IoT Ingestion.
  * `smart-campus/events/access`: Sự kiện quẹt thẻ từ Access Gate.
  * `smart-campus/events/camera`: Sự kiện phát hiện chuyển động từ Camera Stream.
  * `smart-campus/events/core-alert`: Sự kiện cảnh báo nghiệp vụ từ Core Business.
- **Xử lý (Logic chính):**
  * Tăng bộ đếm cho từng nhóm sự kiện tương ứng (`sensor_events`, `access_events`, `camera_events`, `core_alerts`).
  * Phân tích và lưu trữ nhiệt độ và độ ẩm trung bình theo từng vị trí phòng học (`location`). Giới hạn lịch sử đo đạc ở mức 1000 giá trị gần nhất để tránh tràn bộ nhớ.
  * Tính toán tỷ lệ từ chối ra vào (`access_deny_rate_percent`) dựa trên số lượt được phép (`access_granted`) và bị từ chối (`access_denied`).
  * Theo dõi số lượng thiết bị có mức pin yếu ($< 20\%$).
- **Output (Đầu ra):** REST API cung cấp chỉ số tổng hợp tại `GET /api/v1/metrics`, xem từng chỉ số cụ thể tại `GET /api/v1/metrics/{metric_name}` và xem lịch sử các sự kiện gần đây tại `GET /api/v1/events/recent`.
- **Tài liệu tham chiếu:**
  * OpenAPI Spec: `services/analytics/contracts/analytics.openapi.yaml`

### Tiêu chí B: Service chạy ổn định bằng Docker Compose (1.5đ)
- Dịch vụ được định nghĩa dưới tên service `analytics` trong file `docker-compose.yml`.
- Chạy ổn định trong nền thông qua cấu hình `restart: unless-stopped` và mạng `campus-net`.
- Tự động kiểm tra sức khỏe của container bằng `healthcheck` sau mỗi 30 giây.

### Tiêu chí C: Endpoint `/health` hoạt động (1.0đ)
- Endpoint triển khai tại: `GET /health` (Port `8005` ánh xạ vào container port `8000`).
- Phản hồi mẫu (HTTP 200 OK):
  ```json
  {
    "status": "ok",
    "service": "analytics",
    "version": "1.0.0",
    "time": "2026-06-17T02:30:10Z",
    "mqtt_connected": true,
    "total_events": 142
  }
  ```
- Minh chứng đã được chụp ảnh lưu tại `reports/health-local.png`.

### Tiêu chí D: Tích hợp đúng contract với nhóm khác (2.0đ)
- Tích hợp thành công:
  * **MQTT Subscriber:** Đăng ký nhận tin từ 4 topic của các nhóm khác gửi sang thông qua HiveMQ Cloud.
  * **REST Provider:** Cung cấp API dashboard chỉ số thống kê cho các hệ thống client.
- Quá trình subscribe và hiển thị metrics được kiểm chứng qua file `test_integration.py`.

### Tiêu chí E: Payload / request đúng schema (1.0đ)
- Kiểm tra các trường dữ liệu bắt buộc trong payload JSON của sự kiện môi trường, sự kiện quẹt thẻ, sự kiện camera trước khi thực hiện tính toán.
- Định nghĩa kiểu dữ liệu chặt chẽ cho endpoint REST API bằng mô hình Pydantic.

### Tiêu chí F: Có xử lý lỗi / timeout (1.0đ)
- **Bắt lỗi giải nén payload:** Toàn bộ quá trình đăng ký nhận tin nhắn và phân tích JSON từ MQTT được đặt trong khối `try...except`. Nếu đối tác hoặc dịch vụ nguồn phát tin nhắn sai định dạng, Analytics sẽ chỉ log lỗi ra console và bỏ qua tin nhắn đó chứ tuyệt đối không gây treo hay crash luồng lắng nghe chính.
- **Tính toán an toàn:** Kiểm tra giá trị `None` trước khi đưa vào các phép tính toán trung bình hoặc chia cho 0 để bảo vệ tiến trình.
- Tự động đăng ký lại MQTT topic khi mất kết nối.

### Tiêu chí G: Minh chứng đầy đủ (1.5đ)
- Các minh chứng đã chuẩn bị trong thư mục `reports/` gồm:
  * Danh sách container chạy ổn định: `reports/docker-compose-ps.png`
  * Nhật ký log thực tế: `reports/logs-compose.txt`
  * Sẵn sàng tích hợp: `reports/readiness-checklist.md`

### Tiêu chí H: Trình bày demo rõ ràng (1.0đ)
- **Luồng dữ liệu của service:**
  `MQTT topics (sensor, access, camera, alert)` $\rightarrow$ **[Tổng hợp & Tính toán trung bình]** $\rightarrow$ `GET /api/v1/metrics (KPI Dashboard)`
- Quá trình chạy thử demo được tự động hóa tại mục `4` trong script kiểm thử tích hợp `test_integration.py`.
