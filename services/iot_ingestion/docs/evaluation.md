# Đánh giá tiêu chí chấm điểm — A1: IoT Ingestion Service

Bản tài liệu này tự đánh giá và đối chiếu dịch vụ **A1: IoT Ingestion Service** với thang điểm và tiêu chí chấm điểm tích hợp hệ thống.

## Bảng tổng hợp kết quả

| Mã | Tiêu chí | Điểm tối đa | Trạng thái | Điểm tự đánh giá | Minh chứng & Vị trí trong dự án |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **A** | Nghiệp vụ rõ ràng | 1.0 | ✅ Đạt | 1.0 | Vai trò Publisher. Tài liệu nghiệp vụ tại [analysis-ingestion.md](file:///d:/BTL_DV_KetNoi/services/iot_ingestion/docs/analysis-ingestion.md) và [event-contract-sensor.md](file:///d:/BTL_DV_KetNoi/services/iot_ingestion/docs/event-contract-sensor.md). |
| **B** | Chạy ổn định bằng Docker Compose | 1.5 | ✅ Đạt | 1.5 | Định nghĩa service `iot-ingestion` trong `docker-compose.yml`, có cơ chế healthcheck tự động. |
| **C** | Endpoint `/health` hoạt động | 1.0 | ✅ Đạt | 1.0 | API `GET /health` trả về HTTP 200 OK. |
| **D** | Tích hợp đúng contract với nhóm khác | 2.0 | ✅ Đạt | 2.0 | Tích hợp MQTT bất đồng bộ thành công, được kiểm chứng qua file `test_integration.py`. |
| **E** | Payload / request đúng schema | 1.0 | ✅ Đạt | 1.0 | Validate dữ liệu raw và đóng gói dữ liệu processed đúng schema JSON trong tài liệu hợp đồng. |
| **F** | Có xử lý lỗi / timeout | 1.0 | ✅ Đạt | 1.0 | Có bắt lỗi ngoại lệ, ghi log console chi tiết, MQTT tự động kết nối lại. |
| **G** | Minh chứng đầy đủ | 1.5 | ✅ Đạt | 1.5 | Có đầy đủ hình ảnh và log tại thư mục `reports/`. |
| **H** | Trình bày demo rõ ràng | 1.0 | ✅ Đạt | 1.0 | Sử dụng kịch bản test tích hợp của `test_integration.py` làm demo luồng dữ liệu. |
| | **TỔNG CỘNG** | **10.0** | | **10.0/10.0** | |

---

## Chi tiết thực hiện theo từng tiêu chí

### Tiêu chí A: Nghiệp vụ rõ ràng (1.0đ)
- **Vai trò:** Nhận dữ liệu cảm biến môi trường thô (raw) từ cổng phần cứng, chuẩn hóa dữ liệu, đối chiếu danh sách thiết bị và phân loại mức độ an toàn trước khi publish cho các dịch vụ khác sử dụng.
- **Input (Đầu vào):** Tin nhắn MQTT raw từ thiết bị cảm biến gửi lên topic `smart-campus/raw/iot/environment`.
- **Xử lý (Logic chính):**
  * Tải và tra cứu danh sách thiết bị hợp lệ từ tệp `Datas/IoT_device_registry.csv`.
  * Kiểm tra tính hợp lệ của gói tin raw (yêu cầu đầy đủ các trường `event_id`, `event_type`, `timestamp`, `device_id`, `temperature_c`, `humidity_percent`, `motion_detected`).
  * Phân loại trạng thái môi trường (`status`) và cảnh báo (`alert_level`) dựa trên ngưỡng:
    * `sensor_error` nếu thiếu giá trị cảm biến.
    * `invalid_device` nếu ID thiết bị không nằm trong registry whitelist.
    * `danger` nếu nhiệt độ $\ge 40^\circ\text{C}$ hoặc CO2 $\ge 1800\,\text{ppm}$ hoặc khói $\ge 1.0\,\text{ppm}$.
    * `warning` nếu nhiệt độ $\ge 35^\circ\text{C}$ hoặc độ ẩm $\ge 85\%$ hoặc CO2 $\ge 1200\,\text{ppm}$ hoặc khói $\ge 0.5\,\text{ppm}$ hoặc pin $< 20\%$.
    * `normal` cho các trường hợp an toàn còn lại.
- **Output (Đầu ra):** Dữ liệu chuẩn hóa đã phân loại được publish lên topic `smart-campus/events/sensor`.
- **Tài liệu tham chiếu:**
  * OpenAPI: `services/iot_ingestion/contracts/iot-ingestion.openapi.yaml`
  * Event Contract: `services/iot_ingestion/docs/event-contract-sensor.md`

### Tiêu chí B: Service chạy ổn định bằng Docker Compose (1.5đ)
- Service `iot-ingestion` được định nghĩa chạy ổn định trong file `docker-compose.yml` ở thư mục gốc.
- **Cơ chế Healthcheck:**
  ```yaml
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"]
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 10s
  ```
- Khởi động an toàn, tự động khởi chạy lại nếu gặp sự cố thông qua thiết lập `restart: unless-stopped`.

### Tiêu chí C: Endpoint `/health` hoạt động (1.0đ)
- Endpoint triển khai tại: `GET /health` (Port `8001` ánh xạ vào container port `8000`).
- Phản hồi mẫu (HTTP 200 OK):
  ```json
  {
    "status": "ok",
    "service": "iot-ingestion",
    "version": "1.0.0",
    "time": "2026-06-17T02:30:10Z",
    "mqtt_connected": true,
    "message_count": 42
  }
  ```
- Minh chứng đã được chụp ảnh và lưu trữ tại `reports/health-local.png`.

### Tiêu chí D: Tích hợp đúng contract với nhóm khác (2.0đ)
- Tích hợp thành công với các dịch vụ tiêu thụ (Consumer) qua HiveMQ Cloud MQTT Broker:
  * **IoT Ingestion (A1)** $\xrightarrow{\text{MQTT: smart-campus/events/sensor}}$ **Core Business (A6)** và **Analytics (A5)**.
- Kịch bản chạy liên kết đã được kiểm tra độc lập và tự động hóa trong file `test_integration.py`.

### Tiêu chí E: Payload / request đúng schema (1.0đ)
- Toàn bộ dữ liệu processed event trước khi publish đều tuân thủ 100% JSON schema đã cam kết trong file [event-contract-sensor.md](file:///d:/BTL_DV_KetNoi/services/iot_ingestion/docs/event-contract-sensor.md).
- Mã nguồn định nghĩa schema chi tiết tại: `services/iot_ingestion/src/main.py`.

### Tiêu chí F: Có xử lý lỗi / timeout (1.0đ)
- **Cơ chế bắt lỗi:**
  * Toàn bộ quá trình tiếp nhận tin nhắn MQTT và parse JSON được đặt trong các khối `try...except` để tránh việc tin nhắn rác gây crash tiến trình subscribe dữ liệu.
  * Việc load file danh sách thiết bị CSV có cơ chế kiểm tra nhiều đường dẫn khả thi, nếu không tìm thấy sẽ chuyển sang chế độ whitelist trống kèm log cảnh báo chi tiết thay vì dừng chương trình.
  * Trình điều khiển MQTT (`paho-mqtt`) hỗ trợ tự động khôi phục kết nối và đăng ký lại topic khi Broker gặp sự cố mất mạng đột ngột.

### Tiêu chí G: Minh chứng đầy đủ (1.5đ)
- Đầy đủ báo cáo tại thư mục `reports/` bao gồm:
  * Trạng thái container hoạt động: `reports/docker-compose-ps.png`
  * Nhật ký log thực tế: `reports/logs-compose.txt`
  * Sẵn sàng tích hợp: `reports/readiness-checklist.md`

### Tiêu chí H: Trình bày demo rõ ràng (1.0đ)
- **Luồng dữ liệu của service:**
  `MQTT smart-campus/raw/iot/environment` (Dữ liệu raw) $\rightarrow$ **[Kiểm tra Whitelist & Phân loại ngưỡng]** $\rightarrow$ `MQTT smart-campus/events/sensor` (Dữ liệu processed)
- Quá trình chạy thử demo được tự động hóa tại mục `3.1` trong script kiểm thử tích hợp `test_integration.py`.
