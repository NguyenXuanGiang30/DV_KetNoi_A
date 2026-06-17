# Đánh giá tiêu chí chấm điểm — A6: Core Business Service

Bản tài liệu này tự đánh giá và đối chiếu dịch vụ **A6: Core Business Service** với thang điểm và tiêu chí chấm điểm tích hợp hệ thống.

## Bảng tổng hợp kết quả

| Mã | Tiêu chí | Điểm tối đa | Trạng thái | Điểm tự đánh giá | Minh chứng & Vị trí trong dự án |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **A** | Nghiệp vụ rõ ràng | 1.0 | ✅ Đạt | 1.0 | Vai trò Central Brain & Policy Engine. Mô tả nghiệp vụ dưới đây, tài liệu OpenAPI tại `contracts/core-business.openapi.yaml` và Event Contract tại [event-contract-core.md](file:///d:/BTL_DV_KetNoi/services/core_business/docs/event-contract-core.md). |
| **B** | Chạy ổn định bằng Docker Compose | 1.5 | ✅ Đạt | 1.5 | Định nghĩa service `core-business` trong `docker-compose.yml`, quản lý dependency chain và có healthcheck. |
| **C** | Endpoint `/health` hoạt động | 1.0 | ✅ Đạt | 1.0 | API `GET /health` trả về HTTP 200 OK. |
| **D** | Tích hợp đúng contract với nhóm khác | 2.0 | ✅ Đạt | 2.0 | Tích hợp MQTT subscribe, MQTT publish và gọi REST API đồng bộ với Access Gate/Notification thành công. |
| **E** | Payload / request đúng schema | 1.0 | ✅ Đạt | 1.0 | Sử dụng Pydantic models validate dữ liệu REST đầu vào và cấu trúc tin nhắn MQTT đúng định dạng. |
| **F** | Có xử lý lỗi / timeout | 1.0 | ✅ Đạt | 1.0 | Gọi API ngoài bất đồng bộ qua Background Thread, cấu hình HTTP timeout, chống lỗi lan truyền. |
| **G** | Minh chứng đầy đủ | 1.5 | ✅ Đạt | 1.5 | Đầy đủ hình ảnh và log tại thư mục `reports/`. |
| **H** | Trình bày demo rõ ràng | 1.0 | ✅ Đạt | 1.0 | Sử dụng kịch bản test tích hợp của `test_integration.py` làm demo luồng dữ liệu. |
| | **TỔNG CỘNG** | **10.0** | | **10.0/10.0** | |

---

## Chi tiết thực hiện theo từng tiêu chí

### Tiêu chí A: Nghiệp vụ rõ ràng (1.0đ)
- **Vai trò:** Bộ não trung tâm (Core Engine). Đăng ký nhận sự kiện đã xử lý từ các microservices vệ tinh (Cảm biến, Cửa ra vào, Camera), áp dụng luật nghiệp vụ (policy rules) để phát hiện sự cố, sinh cảnh báo hệ thống, publish tin nhắn và gọi dịch vụ cảnh báo ngoài.
- **Input (Đầu vào):** 
  * Đăng ký MQTT: Lắng nghe processed events từ `smart-campus/events/sensor`, `smart-campus/events/access`, và `smart-campus/events/camera`.
  * REST API: Cung cấp API `POST /access/check` cho Access Gate gọi để kiểm tra luật thời gian ra vào.
- **Xử lý (Logic chính):**
  * **Đánh giá sự kiện cảm biến:** Nếu trạng thái là `danger` (vượt ngưỡng) hoặc `sensor_error` (hỏng hóc) hoặc `invalid_device` (thiết bị lạ), Core tự động kích hoạt tạo cảnh báo cấp độ tương ứng.
  * **Đánh giá sự kiện cửa:** Nếu kết quả quẹt thẻ là bị từ chối (`access_result == "denied"`), tạo cảnh báo xâm nhập trái phép.
  * **Đánh giá sự kiện camera:** Nếu phát hiện đối tượng chưa đăng ký (`unknown_person == true`), tạo cảnh báo người lạ xâm nhập.
  * **Luật kiểm soát ra vào:** Kiểm tra khung giờ (chỉ cho phép ra vào trong giờ hành chính từ 06:00 đến 22:00).
- **Output (Đầu ra):**
  * Publish sự kiện cảnh báo hệ thống lên topic MQTT `smart-campus/events/core-alert`.
  * Gọi REST API của dịch vụ Notification tại `POST /api/v1/notifications` để gửi cảnh báo qua các kênh (Console, Telegram).
- **Tài liệu tham chiếu:**
  * OpenAPI Spec: `services/core_business/contracts/core-business.openapi.yaml`
  * Event Contract: `services/core_business/docs/event-contract-core.md`

### Tiêu chí B: Service chạy ổn định bằng Docker Compose (1.5đ)
- Dịch vụ được định nghĩa dưới tên service `core-business` trong file `docker-compose.yml`.
- Do hoạt động dựa trên dữ liệu của các service vệ tinh, `core-business` được cấu hình bắt đầu chạy chỉ khi 3 container liên quan đã healthy:
  ```yaml
  depends_on:
    ai-vision:
      condition: service_healthy
    access-gate:
      condition: service_healthy
    notification:
      condition: service_healthy
  ```
- Có cấu hình `healthcheck` tự động kiểm tra định kỳ để giám sát hoạt động.

### Tiêu chí C: Endpoint `/health` hoạt động (1.0đ)
- Endpoint triển khai tại: `GET /health` (Port `8006` ánh xạ vào container port `8000`).
- Phản hồi mẫu (HTTP 200 OK):
  ```json
  {
    "status": "ok",
    "service": "core-business",
    "version": "1.0.0",
    "time": "2026-06-17T02:30:10Z",
    "mqtt_connected": true,
    "alerts_count": 5
  }
  ```
- Minh chứng đã được chụp ảnh lưu tại `reports/health-local.png`.

### Tiêu chí D: Tích hợp đúng contract với nhóm khác (2.0đ)
- Tích hợp đa liên kết thành công:
  * **MQTT Subscriber:** Lắng nghe 3 topic sự kiện nguồn từ các dịch vụ khác qua HiveMQ Cloud.
  * **MQTT Publisher:** Phát đi sự kiện cảnh báo lên topic `smart-campus/events/core-alert`.
  * **REST Provider:** Cung cấp cổng kiểm tra chính sách cho Access Gate gọi qua REST API.
  * **REST Client:** Gọi đồng bộ dịch vụ Notification gửi cảnh báo qua REST API.
- Đã kiểm thử tích hợp tự động qua file `test_integration.py`.

### Tiêu chí E: Payload / request đúng schema (1.0đ)
- Định nghĩa schema Pydantic chặt chẽ cho `AccessCheckRequest` và `AccessCheckResponse` đảm bảo đúng kiểu dữ liệu.
- Cấu trúc tin nhắn MQTT cảnh báo được định dạng chính xác theo đặc tả đã thống nhất tại file [event-contract-core.md](file:///d:/BTL_DV_KetNoi/services/core_business/docs/event-contract-core.md).

### Tiêu chí F: Có xử lý lỗi / timeout (1.0đ)
- **Cơ chế chống nghẽn & Cô lập lỗi (Fire-and-forget):**
  * Quá trình gửi yêu cầu cảnh báo sang Notification Service qua REST API được đẩy vào một tiến trình luồng phụ (`threading.Thread`) để chạy độc lập. Nếu dịch vụ Notification bị tắt, ngắt kết nối hoặc phản hồi rất chậm, nó cũng không gây block hoặc treo luồng xử lý sự kiện chính của Core Business.
  * Thiết lập timeout cuộc gọi REST API tối đa là 5.0 giây.
  * Các hàm xử lý MQTT event được bảo vệ trong các khối `try...except` giúp hệ thống trung tâm tiếp tục vận hành bền bỉ kể cả khi một dịch vụ đối tác phát tin nhắn sai format.
  * Tự động khôi phục kết nối và đăng ký lại MQTT topic.

### Tiêu chí G: Minh chứng đầy đủ (1.5đ)
- Đầy đủ báo cáo tại thư mục `reports/` bao gồm:
  * Trạng thái container hoạt động: `reports/docker-compose-ps.png`
  * Nhật ký log thực tế: `reports/logs-compose.txt`
  * Sẵn sàng tích hợp: `reports/readiness-checklist.md`

### Tiêu chí H: Trình bày demo rõ ràng (1.0đ)
- **Luồng dữ liệu của service:**
  `MQTT topics (sensor, access, camera)` $\rightarrow$ **[Đánh giá luật nghiệp vụ]** $\rightarrow$ `POST /notifications` & `MQTT smart-campus/events/core-alert`
- Quá trình chạy thử demo được tự động hóa tại mục `2.3` và `3` trong script kiểm thử tích hợp `test_integration.py`.
