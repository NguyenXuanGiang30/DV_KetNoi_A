# Hướng Dẫn Trình Bày Demo — A6: Core Business Service

Bản tài liệu này hướng dẫn chi tiết kịch bản thuyết trình và bảo vệ đồ án tích hợp hệ thống cho nhóm phụ trách dịch vụ **Core Business Service (A6)** theo quy trình 6 bước chuẩn.

---

## 1. Vai trò của nhóm
* **Tên dịch vụ:** Core Business Service (A6).
* **Vai trò trong hệ thống Smart Campus:**
  * Bộ não trung tâm đưa ra quyết định nghiệp vụ (Central Brain).
  * Lắng nghe và liên kết các sự kiện từ các nhánh độc lập (Cảm biến, Cửa ra vào, Camera an ninh).
  * Đánh giá các sự cố dựa trên chính sách (Policy Rules) về an ninh, an toàn phòng cháy và thời gian hoạt động.
  * Kích hoạt quy trình phản ứng nhanh khi xảy ra sự cố (phát đi sự kiện cảnh báo hệ thống, gọi gửi thông báo khẩn cấp).
* **Mô hình giao tiếp:** Đóng vai trò là **MQTT Consumer** (nhận tin từ 3 topic), **REST Provider** (check chính sách cho Access Gate), **REST Client** (gọi Notification API), và **MQTT Publisher** (gửi tin cảnh báo).

---

## 2. Input
* **Dữ liệu nhận (MQTT):**
  * Sự kiện môi trường (`smart-campus/events/sensor`).
  * Sự kiện quẹt thẻ RFID (`smart-campus/events/access`).
  * Sự kiện camera an ninh (`smart-campus/events/camera`).
* **Dữ liệu nhận (REST):** Nhận request đồng bộ từ Access Gate tại endpoint `POST /access/check` để kiểm tra chính sách thẻ.
* **Nguồn gửi:** Gửi bất đồng bộ từ các microservices A1, A2, A3 qua MQTT và đồng bộ từ A3 qua REST HTTP.

---

## 3. Xử lý nghiệp vụ
* **Đánh giá luật an toàn môi trường:** Khi nhận tin từ `events/sensor`, kiểm tra trường `status`. Nếu bằng `"danger"` (khí gas rò rỉ, cháy nổ), tự động sinh sự kiện cảnh báo khẩn cấp cấp độ `CRITICAL`.
* **Đánh giá luật kiểm soát an ninh cửa:** Khi nhận tin từ `events/access`, kiểm tra trường `access_result`. Nếu bằng `"denied"`, ghi nhận nguy cơ đột nhập.
* **Đánh giá luật thị giác máy tính:** Khi nhận tin từ `events/camera`, kiểm tra trường `unknown_person`. Nếu bằng `true` và không so khớp được khuôn mặt tham chiếu, tạo cảnh báo người lạ xâm nhập.
* **Đánh giá luật khung giờ ra vào:** Khi Access Gate gọi API `POST /access/check`, kiểm tra thời gian hiện tại:
  * Cho phép (`status = approved`) nếu trong giờ làm việc (06:00 - 22:00).
  * Từ chối (`status = rejected`, lý do: `outside_business_hours`) nếu ngoài khung giờ hành chính.
* **Đồng bộ hóa lịch sử:** Định kỳ gọi REST API `GET /access/logs/recent` của Access Gate để kéo lịch sử sự kiện cửa về đối chiếu.

---

## 4. Output
* **Dữ liệu trả ra:**
  * **Publish MQTT:** Sự kiện cảnh báo hệ thống (Core Alert Event):
    ```json
    {
      "id": "alert-99999",
      "source_service": "core-business",
      "alert_type": "FIRE_HAZARD",
      "severity": "CRITICAL",
      "message": "🚨 CẢNH BÁO CHÁY: Phát hiện nhiệt độ 41.5°C tại Lab room 102",
      "related_event_id": "proc-env-98765",
      "status": "OPEN",
      "created_at": "2026-06-17T02:30:10Z",
      "resolved_at": null
    }
    ```
  * **REST Response:** Trả về quyết định kiểm duyệt truy cập cho Access Gate (`approved`/`rejected`).

---

## 5. Output gửi cho ai?
* **MQTT:** Publish lên topic `smart-campus/events/core-alert` cho **Analytics (A5)** thu thập số liệu.
* **REST API:** Gọi đồng bộ tới API `POST /api/v1/notifications` của **Notification Service (A7)** để kích hoạt gửi tin Telegram, SMS đến ban bảo vệ trường.

---

## 6. Minh chứng demo
* **Container running:** Chạy lệnh `docker compose ps` để kiểm tra container `core-business` đang ở trạng thái *Up (healthy)*.
* **Health endpoint:** `GET http://localhost:8006/health`.
* **Demo kịch bản tích hợp và Chống lỗi lan truyền (Tiêu chí F):**
  * Trong log của `core-business`, khi phát hiện một cảm biến báo trạng thái nguy hại (`danger`), log sẽ hiển thị rõ:
    `[Policy] Sensor ENV-SEN-LAB102 triggered danger status. Severity: CRITICAL.`
    `[MQTT-Pub] Publishing core-alert to topic smart-campus/events/core-alert...`
    `[Thread-Trigger] Dispatching REST notification call to Notification service...`
  * Để minh chứng khả năng cô lập lỗi: Việc gọi gửi tin sang dịch vụ Notification được chạy trong một **Thread phụ độc lập** (`threading.Thread`) với timeout HTTP tối đa 5 giây. Nếu dịch vụ Notification bị sập, luồng chính xử lý MQTT của Core Business vẫn chạy liên tục không bị nghẽn hay crash.
 Oregon
