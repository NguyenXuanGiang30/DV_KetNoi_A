# Đánh giá tiêu chí chấm điểm — A4: AI Vision Service

Bản tài liệu này tự đánh giá và đối chiếu dịch vụ **A4: AI Vision Service** với thang điểm và tiêu chí chấm điểm tích hợp hệ thống.

## Bảng tổng hợp kết quả

| Mã | Tiêu chí | Điểm tối đa | Trạng thái | Điểm tự đánh giá | Minh chứng & Vị trí trong dự án |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **A** | Nghiệp vụ rõ ràng | 1.0 | ✅ Đạt | 1.0 | Vai trò REST Provider. Định nghĩa API trong `contracts/ai-vision.openapi.yaml` và mã nguồn `src/main.py`. |
| **B** | Chạy ổn định bằng Docker Compose | 1.5 | ✅ Đạt | 1.5 | Khai báo service `ai-vision` trong `docker-compose.yml`, có cơ chế healthcheck. |
| **C** | Endpoint `/health` hoạt động | 1.0 | ✅ Đạt | 1.0 | API `GET /health` trả về HTTP 200 OK. |
| **D** | Tích hợp đúng contract với nhóm khác | 2.0 | ✅ Đạt | 2.0 | Tích hợp REST thành công với Camera Stream (`/detect`) và Core Business (`/vision/face-match`). |
| **E** | Payload / request đúng schema | 1.0 | ✅ Đạt | 1.0 | Sử dụng Pydantic models validate nghiêm ngặt và phản hồi đúng chuẩn ProblemDetails RFC 7807 khi gặp lỗi. |
| **F** | Có xử lý lỗi / timeout | 1.0 | ✅ Đạt | 1.0 | Xác thực token, xử lý ngoại lệ đầu vào không hợp lệ để tránh crash hệ thống. |
| **G** | Minh chứng đầy đủ | 1.5 | ✅ Đạt | 1.5 | Đầy đủ hình ảnh và log tại thư mục `reports/`. |
| **H** | Trình bày demo rõ ràng | 1.0 | ✅ Đạt | 1.0 | Sử dụng kịch bản test tích hợp của `test_integration.py` làm demo luồng dữ liệu. |
| | **TỔNG CỘNG** | **10.0** | | **10.0/10.0** | |

---

## Chi tiết thực hiện theo từng tiêu chí

### Tiêu chí A: Nghiệp vụ rõ ràng (1.0đ)
- **Vai trò:** Cung cấp các chức năng trí tuệ nhân tạo phân tích hình ảnh, phát hiện vật thể (object detection) từ camera và đối chiếu so khớp khuôn mặt (face-matching) phục vụ kiểm soát ra vào.
- **Input (Đầu vào):** 
  * API `/detect`: Nhận thông tin camera, URL ảnh hoặc dữ liệu ảnh Base64.
  * API `/vision/face-match`: Nhận thông tin camera, ảnh đầu vào và ID khuôn mặt gốc làm tham chiếu (`reference_face_id`).
- **Xử lý (Logic chính):**
  * Mô phỏng thuật toán nhận diện vật thể: Phân tích ảnh để tìm các nhãn (`person`, `vehicle`, `unknown`), tính toán độ tin cậy `confidence` ngẫu nhiên từ 0.70 - 0.99, tính toán bounding box và đánh giá mức độ rủi ro (`risk_level: low/medium/high`).
  * Mô phỏng so khớp khuôn mặt: Tính toán độ tương đồng và quyết định kết quả trùng khớp (`matched: true/false`).
- **Output (Đầu ra):** JSON chứa thông tin nhận diện chi tiết, kết quả đối chiếu, bounding box và độ tin cậy.
- **Tài liệu tham chiếu:**
  * OpenAPI Spec: `services/ai_vision/contracts/ai-vision.openapi.yaml`

### Tiêu chí B: Service chạy ổn định bằng Docker Compose (1.5đ)
- Dịch vụ được định nghĩa dưới tên service `ai-vision` trong file `docker-compose.yml`.
- Chạy độc lập, không phụ thuộc vào khởi động của các service khác, giúp hệ thống luôn sẵn sàng nhận lệnh phân tích.
- Tích hợp `healthcheck` tự động thăm dò cổng 8000 của container.

### Tiêu chí C: Endpoint `/health` hoạt động (1.0đ)
- Endpoint triển khai tại: `GET /health` (Port `8004` ánh xạ vào container port `8000`).
- Phản hồi mẫu (HTTP 200 OK):
  ```json
  {
    "status": "ok",
    "service": "ai-vision",
    "version": "1.0.0",
    "time": "2026-06-17T02:30:10Z"
  }
  ```
- Minh chứng đã được chụp ảnh lưu tại `reports/health-local.png`.

### Tiêu chí D: Tích hợp đúng contract với nhóm khác (2.0đ)
- Tích hợp REST API đồng bộ thành công với các dịch vụ khác:
  * **AI Vision (A4)** $\xleftarrow{\text{POST /detect}}$ **Camera Stream (A2)**.
  * **AI Vision (A4)** $\xleftarrow{\text{POST /vision/face-match}}$ **Core Business (A6)**.
- Quá trình gọi và nhận phản hồi thực tế đã được chạy tự động trong file test tích hợp `test_integration.py`.

### Tiêu chí E: Payload / request đúng schema (1.0đ)
- Sử dụng thư viện Pydantic để định nghĩa chặt chẽ kiểu dữ liệu cho `DetectionRequest`, `FaceMatchRequest` và các schema con như `BBox`, `DetectionItem`.
- Khi client gửi dữ liệu không hợp lệ (như thiếu cả `image_url` và `image_base64` khi gọi `/detect`), API sẽ trả về lỗi HTTP 400 và cấu trúc lỗi tuân thủ đặc tả chuẩn hóa **Problem Details (RFC 7807)**:
  ```json
  {
    "type": "https://smart-campus.local/problems/invalid-image",
    "title": "Invalid image",
    "status": 400,
    "detail": "image_url or image_base64 is required",
    "instance": "/detect"
  }
  ```

### Tiêu chí F: Có xử lý lỗi / timeout (1.0đ)
- **Cơ chế xác thực:** Bảo vệ tất cả các API nghiệp vụ bằng token xác thực `Bearer` trong header. Nếu thiếu hoặc token sai, API phản hồi lỗi HTTP 401 theo chuẩn Problem Details mà không làm crash ứng dụng.
- **Bắt lỗi nghiệp vụ:** Kiểm tra và bắt lỗi dữ liệu đầu vào không hợp lệ (ví dụ: truy vấn kết quả nhận diện không tồn tại trả về lỗi HTTP 404 có cấu trúc).

### Tiêu chí G: Minh chứng đầy đủ (1.5đ)
- Đầy đủ báo cáo tại thư mục `reports/` bao gồm:
  * Trạng thái container hoạt động: `reports/docker-compose-ps.png`
  * Nhật ký log thực tế: `reports/logs-compose.txt`
  * Sẵn sàng tích hợp: `reports/readiness-checklist.md`

### Tiêu chí H: Trình bày demo rõ ràng (1.0đ)
- **Luồng dữ liệu của service:**
  `POST Request (image)` $\rightarrow$ **[Mock AI Detection & Face Match]** $\rightarrow$ `HTTP REST Response (detections / match status)`
- Quá trình chạy thử demo được tự động hóa tại mục `2.1` và `2.2` trong script kiểm thử tích hợp `test_integration.py`.
