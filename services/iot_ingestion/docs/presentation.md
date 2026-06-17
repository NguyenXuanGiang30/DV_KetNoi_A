# Hướng Dẫn Trình Bày Demo — A1: IoT Ingestion Service

Bản tài liệu này hướng dẫn chi tiết kịch bản thuyết trình và bảo vệ đồ án tích hợp hệ thống cho nhóm phụ trách dịch vụ **IoT Ingestion Service (A1)** theo quy trình 6 bước chuẩn.

---

## 1. Vai trò của nhóm
* **Tên dịch vụ:** IoT Ingestion Service (A1).
* **Vai trò trong hệ thống Smart Campus:** 
  * Tiếp nhận dữ liệu cảm biến môi trường thô từ các thiết bị ngoại vi hoặc simulator giả lập.
  * Làm sạch, chuẩn hóa cấu trúc dữ liệu.
  * Đối chiếu whitelist thiết bị hợp lệ để loại bỏ thiết bị lạ/giả mạo.
  * Đánh giá ngưỡng để phân loại trạng thái môi trường và đưa ra cấp độ cảnh báo tức thời.
* **Mô hình giao tiếp:** Đóng vai trò là cả **Consumer** (nhận tin nhắn raw) và **Publisher/Provider** (phát tin nhắn chuẩn hóa cho các dịch vụ khác sử dụng).

---

## 2. Input
* **Dữ liệu nhận:** Gói tin JSON thô chứa các trường thông tin cảm biến môi trường:
  ```json
  {
    "event_id": "raw-env-12345",
    "event_type": "iot.sensor.raw",
    "timestamp": "2026-06-17T02:30:10Z",
    "device_id": "ENV-SEN-LAB102",
    "temperature_c": 41.5,
    "humidity_percent": 65.0,
    "co2_ppm": 1250,
    "smoke_level_ppm": 0.2,
    "battery_percent": 95
  }
  ```
* **Nguồn gửi:** Các thiết bị cảm biến vật lý tại phòng Lab hoặc bộ simulator giả lập phần cứng.
* **Giao thức:** Nhận bất đồng bộ qua MQTT topic: `smart-campus/raw/iot/environment` trên HiveMQ Cloud Broker.

---

## 3. Xử lý nghiệp vụ
* **Kiểm tra & Validate dữ liệu:** Kiểm tra tính toàn vẹn của gói tin JSON. Đảm bảo chứa đầy đủ các trường thông tin bắt buộc (`device_id`, `temperature_c`, v.v.).
* **Đối chiếu Whitelist:** Tải danh sách thiết bị hợp lệ từ tệp CSV whitelist `/app/data/IoT_device_registry.csv`. Tra cứu `device_id` nhận được:
  * Nếu không tìm thấy $\rightarrow$ Đánh dấu trạng thái `"status": "invalid_device"` và cấp độ cảnh báo `"alert_level": "WARNING"`.
* **Phân loại trạng thái an toàn môi trường:** Áp dụng các luật logic nghiệp vụ dựa trên ngưỡng:
  * Trạng thái `danger` (Cảnh báo cháy/Nguy hiểm): Nếu nhiệt độ $\ge 40^\circ\text{C}$ hoặc CO2 $\ge 1800\,\text{ppm}$ hoặc khói $\ge 1.0\,\text{ppm}$.
  * Trạng thái `warning` (Cảnh báo bất thường): Nếu nhiệt độ $\ge 35^\circ\text{C}$ hoặc độ ẩm $\ge 85\%$ hoặc CO2 $\ge 1200\,\text{ppm}$ hoặc khói $\ge 0.5\,\text{ppm}$ hoặc pin $< 20\%$.
  * Trạng thái `normal` (An toàn): Trong các trường hợp còn lại.
  * Trạng thái `sensor_error` nếu thiếu hoặc sai hỏng thông số đo đạc.

---

## 4. Output
* **Dữ liệu trả ra:** Gói tin JSON chuẩn hóa (Processed Sensor Event) bổ sung thêm các trường phân tích nghiệp vụ:
  ```json
  {
    "event_id": "proc-env-98765",
    "event_type": "iot.sensor.processed",
    "source_service": "iot-ingestion",
    "timestamp": "2026-06-17T02:30:10Z",
    "device_id": "ENV-SEN-LAB102",
    "metrics": {
      "temperature_c": 41.5,
      "humidity_percent": 65.0,
      "co2_ppm": 1250,
      "smoke_level_ppm": 0.2,
      "battery_percent": 95
    },
    "status": "danger",
    "alert_level": "CRITICAL"
  }
  ```

---

## 5. Output gửi cho ai?
* **Cách thức gửi:** Gửi bất đồng bộ bằng cách publish lên MQTT broker.
* **Topic publish:** `smart-campus/events/sensor`.
* **Bên nhận tiếp theo (Consumer):**
  * **Core Business (A6):** Nhận tin để áp dụng chính sách phản ứng an toàn (kích hoạt cảnh báo cháy, gửi thông báo).
  * **Analytics (A5):** Nhận tin để cập nhật bộ đếm và tính toán nhiệt độ/độ ẩm trung bình cho Dashboard.

---

## 6. Minh chứng demo
* **Container running:** Chạy lệnh `docker compose ps` để chứng minh container `iot-ingestion` đang chạy ổn định.
* **Health endpoint:** Truy vấn `GET http://localhost:8001/health` để chứng minh service đang hoạt động tốt (HTTP 200 OK) và hiển thị số lượng tin nhắn đã xử lý:
  ```json
  {
    "status": "ok",
    "service": "iot-ingestion",
    "version": "1.0.0",
    "time": "2026-06-17T02:30:10Z",
    "mqtt_connected": true,
    "message_count": 12
  }
  ```
* **Log xử lý:** Console hiển thị rõ quá trình:
  `[MQTT-Sub] Nhận tin thô từ smart-campus/raw/iot/environment...`
  `[Process] Đối chiếu whitelist thiết bị ENV-SEN-LAB102: Hợp lệ.`
  `[Process] Phát hiện nhiệt độ 41.5°C >= 40.0°C. Phân loại status: danger, alert_level: CRITICAL`
  `[MQTT-Pub] Phát tin chuẩn hóa lên topic smart-campus/events/sensor`
