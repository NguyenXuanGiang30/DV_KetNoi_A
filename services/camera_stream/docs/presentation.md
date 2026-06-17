# Hướng Dẫn Trình Bày Demo — A2: Camera Stream Service

Bản tài liệu này hướng dẫn chi tiết kịch bản thuyết trình và bảo vệ đồ án tích hợp hệ thống cho nhóm phụ trách dịch vụ **Camera Stream Service (A2)** theo quy trình 6 bước chuẩn.

---

## 1. Vai trò của nhóm
* **Tên dịch vụ:** Camera Stream Service (A2).
* **Vai trò trong hệ thống Smart Campus:**
  * Kết nối và giám sát luồng video thời gian thực từ các camera trong khuôn viên.
  * Phân tích và phát hiện chuyển động (motion detection) nhằm giảm tải tần suất gọi mô hình AI.
  * Gọi dịch vụ AI Vision để nhận diện vật thể/người khi có biến động.
  * Phát tín hiệu sự kiện camera an ninh cho hệ thống trung tâm.
* **Mô hình giao tiếp:** Đóng vai trò là **REST Client** (gọi dịch vụ AI Vision) và **MQTT Publisher** (gửi sự kiện camera).

---

## 2. Input
* **Dữ liệu nhận:** Luồng video liên tục định dạng MJPEG Stream.
* **Nguồn gửi:** URL camera cấu hình qua biến môi trường `CAMERA_STREAM_URL` (ví dụ: luồng camera giám sát hành lang/phòng Lab).
* **Giao thức:** Kết nối HTTP Stream đồng bộ.

---

## 3. Xử lý nghiệp vụ
* **Đọc & Tiền xử lý Frame:** Trích xuất các khung hình (frame) độc lập từ luồng MJPEG. Nhằm tránh quá tải, hệ thống chỉ lấy 1 frame sau mỗi chu kỳ thời gian nhất định (mặc định 2 giây).
* **Thuật toán phát hiện chuyển động:** Sử dụng thuật toán so sánh sai lệch khung hình (Frame Differencing) sau khi chuyển ảnh về dạng xám (grayscale) và áp dụng làm mịn (Gaussian Blur). Tính toán tỷ lệ chuyển động `motion_score` (từ 0.0 đến 1.0).
* **Cooldown Rate-Limiting:** Áp dụng thời gian cooldown tối thiểu (mặc định 10 giây) để lọc các chuyển động liên tục của cùng một sự kiện, tránh Spam API AI Vision.
* **Tích hợp AI REST API:** Nếu `motion_score` vượt ngưỡng (mặc định 0.50), gửi ảnh (Base64 hoặc URL) sang dịch vụ AI Vision qua endpoint `POST /detect` để phân tích vật thể.

---

## 4. Output
* **Dữ liệu trả ra:** JSON Camera Event mô tả sự kiện phát hiện chuyển động kèm kết quả phân tích nhận dạng của AI:
  ```json
  {
    "event_id": "cam-evt-56789",
    "event_type": "camera.motion.processed",
    "source_service": "camera-stream",
    "camera_id": "CAM-HALLWAY-01",
    "timestamp": "2026-06-17T02:30:10Z",
    "location": "Hallway Zone A",
    "motion_detected": true,
    "motion_score": 0.76,
    "ai_status": "success",
    "detections": [
      {
        "label": "person",
        "confidence": 0.94,
        "bbox": [100, 150, 300, 450],
        "risk_level": "medium"
      }
    ],
    "unknown_person": false,
    "risk_level": "medium"
  }
  ```

---

## 5. Output gửi cho ai?
* **Cách thức gửi:** Gửi tin bất đồng bộ lên MQTT broker.
* **Topic publish:** `smart-campus/events/camera`.
* **Bên nhận tiếp theo (Consumer):**
  * **Core Business (A6):** Nhận tin để phát hiện các mối nguy cơ (ví dụ: phát hiện vật thể lạ hoặc người lạ xâm nhập).
  * **Analytics (A5):** Nhận tin để lưu thống kê số lượng chuyển động và phục vụ vẽ biểu đồ an ninh.

---

## 6. Minh chứng demo
* **Container running:** Chạy lệnh `docker compose ps` để kiểm tra container `camera-stream` đang chạy ổn định.
* **Health endpoint:** Truy cập `GET http://localhost:8002/health` trả về HTTP 200 OK cùng thông tin số lượt phát hiện chuyển động:
  ```json
  {
    "status": "ok",
    "service": "camera-stream",
    "version": "1.0.0",
    "time": "2026-06-17T02:30:10Z",
    "stream_connected": true,
    "motion_triggers": 8
  }
  ```
* **Log xử lý và Xử lý lỗi (Graceful Degradation):**
  * Log hiển thị tiến trình: `Motion detected (score: 0.76) -> Calling AI Vision /detect...`
  * Để demo khả năng tự phục hồi và chống crash (Tiêu chí F): Ta có thể tắt tạm thời container `ai-vision`. Log console của `camera-stream` sẽ hiển thị cảnh báo `⚠️ AI Vision service unreachable. Falling back...` và tin nhắn MQTT vẫn được gửi đi với giá trị `"ai_status": "unavailable"`, đảm bảo hệ thống không bị crash.
 Oregon
