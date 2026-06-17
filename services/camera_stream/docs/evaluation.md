# Đánh giá tiêu chí chấm điểm — A2: Camera Stream Service

Bản tài liệu này tự đánh giá và đối chiếu dịch vụ **A2: Camera Stream Service** với thang điểm và tiêu chí chấm điểm tích hợp hệ thống.

## Bảng tổng hợp kết quả

| Mã | Tiêu chí | Điểm tối đa | Trạng thái | Điểm tự đánh giá | Minh chứng & Vị trí trong dự án |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **A** | Nghiệp vụ rõ ràng | 1.0 | ✅ Đạt | 1.0 | Vai trò Publisher & REST Consumer. Tài liệu tại [CameraStreamREADME.md](file:///d:/BTL_DV_KetNoi/Datas/CameraStreamREADME.md) và [event-contract-camera.md](file:///d:/BTL_DV_KetNoi/services/camera_stream/docs/event-contract-camera.md). |
| **B** | Chạy ổn định bằng Docker Compose | 1.5 | ✅ Đạt | 1.5 | Định nghĩa service `camera-stream` trong `docker-compose.yml`, có healthcheck và dependency chain. |
| **C** | Endpoint `/health` hoạt động | 1.0 | ✅ Đạt | 1.0 | API `GET /health` trả về HTTP 200 OK. |
| **D** | Tích hợp đúng contract với nhóm khác | 2.0 | ✅ Đạt | 2.0 | Tích hợp REST với AI Vision (`/detect`) và MQTT với Analytics thành công. |
| **E** | Payload / request đúng schema | 1.0 | ✅ Đạt | 1.0 | Sử dụng dữ liệu đúng JSON schema thống nhất với AI Vision và Analytics. |
| **F** | Có xử lý lỗi / timeout | 1.0 | ✅ Đạt | 1.0 | Có HTTP timeout, cơ chế bắt lỗi khi AI Vision gặp sự cố không gây crash tiến trình đọc camera. |
| **G** | Minh chứng đầy đủ | 1.5 | ✅ Đạt | 1.5 | Đầy đủ hình ảnh và log tại thư mục `reports/`. |
| **H** | Trình bày demo rõ ràng | 1.0 | ✅ Đạt | 1.0 | Sử dụng kịch bản test tích hợp của `test_integration.py` làm demo luồng dữ liệu. |
| | **TỔNG CỘNG** | **10.0** | | **10.0/10.0** | |

---

## Chi tiết thực hiện theo từng tiêu chí

### Tiêu chí A: Nghiệp vụ rõ ràng (1.0đ)
- **Vai trò:** Trung gian nhận luồng MJPEG video từ camera, đọc frame, áp dụng thuật toán phát hiện chuyển động (motion detection) nhằm giảm tần suất và lọc các frame tĩnh, gọi API AI Vision để phân tích ảnh và publish kết quả tích hợp lên MQTT.
- **Input (Đầu vào):** Luồng camera MJPEG từ URL camera cấu hình qua biến môi trường `CAMERA_STREAM_URL`.
- **Xử lý (Logic chính):**
  * Kết nối và capture frame từ luồng camera.
  * Giảm tần suất xử lý (chỉ lấy 1 frame mỗi 2 giây - cấu hình qua `FRAME_INTERVAL`).
  * Thực hiện phát hiện chuyển động bằng thuật toán so sánh frame (sử dụng OpenCV grayscale frame difference hoặc giả lập thông số có độ tin cậy tương đương).
  * Kiểm soát thời gian cooldown giữa các lần gọi AI (tối thiểu 10 giây qua `COOLDOWN_SECONDS`) nhằm tránh quá tải cho service AI Vision.
  * Khi phát hiện chuyển động vượt ngưỡng `MOTION_THRESHOLD` (mặc định 0.50): Gửi ảnh sang AI Vision bằng HTTP REST POST `/detect`.
- **Output (Đầu ra):** Publish kết quả chứa nhận diện vật thể, thông tin đối tượng và mức độ rủi ro lên topic MQTT `smart-campus/events/camera`.
- **Tài liệu tham chiếu:**
  * Hướng dẫn nghiệp vụ: `Datas/CameraStreamREADME.md`
  * Event Contract: `services/camera_stream/docs/event-contract-camera.md`

### Tiêu chí B: Service chạy ổn định bằng Docker Compose (1.5đ)
- Service `camera-stream` được khai báo trong file `docker-compose.yml` ở thư mục gốc.
- Do phụ thuộc vào AI Vision để thực hiện phát hiện vật thể, `camera-stream` được cấu hình ràng buộc khởi động chỉ khi container `ai-vision` đã hoàn toàn ở trạng thái healthy:
  ```yaml
  depends_on:
    ai-vision:
      condition: service_healthy
  ```
- Có cấu hình `healthcheck` tự động kiểm tra định kỳ 30 giây một lần.

### Tiêu chí C: Endpoint `/health` hoạt động (1.0đ)
- Endpoint triển khai tại: `GET /health` (Port `8002` ánh xạ vào container port `8000`).
- Phản hồi mẫu (HTTP 200 OK):
  ```json
  {
    "status": "ok",
    "service": "camera-stream",
    "version": "1.0.0",
    "time": "2026-06-17T02:30:10Z",
    "stream_connected": true,
    "motion_triggers": 12
  }
  ```
- Minh chứng đã được chụp ảnh lưu tại `reports/health-local.png`.

### Tiêu chí D: Tích hợp đúng contract với nhóm khác (2.0đ)
- Tích hợp 2 chiều thành công:
  * **REST Client:** Gửi yêu cầu phát hiện vật thể đồng bộ qua REST: `Camera Stream (A2)` $\xrightarrow{\text{POST /detect}}$ `AI Vision (A4)`.
  * **MQTT Publisher:** Phát đi sự kiện xử lý camera: `Camera Stream (A2)` $\xrightarrow{\text{MQTT: smart-campus/events/camera}}$ `Analytics (A5)` và `Core Business (A6)`.
- Đã kiểm thử tích hợp tự động bằng tệp `test_integration.py`.

### Tiêu chí E: Payload / request đúng schema (1.0đ)
- Request gửi tới AI Vision tuân thủ đúng định dạng `DetectionRequest` (gồm `camera_id`, `image_url` hoặc `image_base64`, `timestamp`, `motion_score`).
- Payload gửi lên MQTT khớp hoàn toàn với thiết kế trong file [event-contract-camera.md](file:///d:/BTL_DV_KetNoi/services/camera_stream/docs/event-contract-camera.md).

### Tiêu chí F: Có xử lý lỗi / timeout (1.0đ)
- **Cơ chế timeout:** Thiết lập timeout tối đa là 5.0 giây khi thực hiện cuộc gọi REST API sang AI Vision thông qua thư viện `httpx`.
- **Cơ chế bắt lỗi & Dự phòng:**
  * Bắt các lỗi ngoại lệ `httpx.TimeoutException` và `httpx.RequestError` để ngăn ngừa dịch vụ bị dừng đột ngột (crash) khi dịch vụ AI Vision gặp sự cố.
  * Nếu không gọi được AI Vision, chương trình tự động ghi nhận cảnh báo, tăng biến đếm lỗi `ai_failures`, đồng thời fallback bằng cách đính kèm trường `"ai_status": "unavailable"` trong payload gửi MQTT, giữ cho hệ thống camera luôn vận hành ổn định.

### Tiêu chí G: Minh chứng đầy đủ (1.5đ)
- Đầy đủ báo cáo tại thư mục `reports/` bao gồm:
  * Trạng thái container hoạt động: `reports/docker-compose-ps.png`
  * Nhật ký log thực tế: `reports/logs-compose.txt`
  * Sẵn sàng tích hợp: `reports/readiness-checklist.md`

### Tiêu chí H: Trình bày demo rõ ràng (1.0đ)
- **Luồng dữ liệu của service:**
  `Camera MJPEG Stream` $\rightarrow$ **[Motion Detection & Cooldown]** $\rightarrow$ `POST /detect (AI Vision)` $\rightarrow$ `MQTT smart-campus/events/camera`
- Quá trình chạy thử demo được tự động hóa tại mục `2.1` trong script kiểm thử tích hợp `test_integration.py`.
