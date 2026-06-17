# Hướng Dẫn Trình Bày Demo — A5: Analytics Service

Bản tài liệu này hướng dẫn chi tiết kịch bản thuyết trình và bảo vệ đồ án tích hợp hệ thống cho nhóm phụ trách dịch vụ **Analytics Service (A5)** theo quy trình 6 bước chuẩn.

---

## 1. Vai trò của nhóm
* **Tên dịch vụ:** Analytics Service (A5).
* **Vai trò trong hệ thống Smart Campus:**
  * Thu thập toàn bộ các sự kiện hoạt động diễn ra trong trường học.
  * Phân tích và tổng hợp các chỉ số đo lường hiệu năng cốt lõi (KPIs) thời gian thực.
  * Hỗ trợ ban quản lý giám sát trạng thái an toàn, an ninh và môi trường trong toàn bộ khuôn viên thông qua giao diện số liệu.
* **Mô hình giao tiếp:** Đóng vai trò là **MQTT Consumer** (nhận tin từ 4 topic sự kiện nguồn) và **REST Provider** (cung cấp API số liệu thống kê).

---

## 2. Input
* **Dữ liệu nhận (MQTT):**
  * Sự kiện môi trường (`smart-campus/events/sensor` từ A1).
  * Sự kiện quẹt thẻ cửa (`smart-campus/events/access` từ A3).
  * Sự kiện phát hiện camera (`smart-campus/events/camera` từ A2).
  * Sự kiện cảnh báo hệ thống (`smart-campus/events/core-alert` từ A6).
* **Nguồn gửi:** Gửi bất đồng bộ từ các microservices A1, A2, A3, A6.
* **Giao thức:** Đăng ký nhận tin qua HiveMQ Cloud MQTT Broker.

---

## 3. Xử lý nghiệp vụ
* **Giải mã & Phân tích tin nhắn:** Nhận gói tin JSON từ hàng đợi, giải nén và phân tích cấu trúc dữ liệu.
* **Cộng dồn bộ đếm (Metrics Counting):** Tăng bộ đếm tổng số lượng sự kiện tương ứng cho từng nhóm chức năng.
* **Tính toán chỉ số trung bình thời gian thực:**
  * Phân loại dữ liệu đo đạc (nhiệt độ, độ ẩm) theo phòng học (`location`).
  * Thực hiện tính toán trung bình cộng của các chỉ số này. Để tránh tràn bộ nhớ trong môi trường chạy lâu dài, danh sách lưu trữ lịch sử được giới hạn tối đa 1000 bản ghi gần nhất.
* **Đo lường bảo mật & thiết bị:**
  * Tính toán tỷ lệ phần trăm từ chối truy cập cửa (`access_deny_rate_percent`) dựa trên số lượt `granted` và `denied`.
  * Theo dõi và cập nhật số lượng cảm biến có dung lượng pin yếu ($< 20\%$).

---

## 4. Output
* **Dữ liệu trả ra:** Các chỉ số KPI tổng hợp của hệ thống dưới dạng JSON response:
  ```json
  {
    "total_events_received": 142,
    "events_by_type": {
      "sensor": 80,
      "access": 45,
      "camera": 12,
      "core_alert": 5
    },
    "average_metrics_by_location": {
      "Lab room 102": {
        "avg_temperature_c": 26.5,
        "avg_humidity_percent": 62.4,
        "data_points_count": 80
      }
    },
    "access_kpis": {
      "total_swipes": 45,
      "granted": 40,
      "denied": 5,
      "deny_rate_percent": 11.11
    },
    "low_battery_devices_count": 1
  }
  ```

---

## 5. Output gửi cho ai?
* **Bên nhận:** Trả về kết quả JSON thông qua HTTP Response đồng bộ khi nhận được yêu cầu truy vấn API.
* **Cổng API:** Endpoint `GET /api/v1/metrics` và `GET /api/v1/metrics/{metric_name}`.
* **Đối tượng nhận tiếp theo:** Màn hình Dashboard quản lý, Web client hiển thị đồ thị của quản trị viên.

---

## 6. Minh chứng demo
* **Container running:** Chạy lệnh `docker compose ps` để kiểm tra container `analytics` đang chạy ổn định.
* **Health endpoint:** `GET http://localhost:8005/health` trả về trạng thái ok.
* **Minh chứng số liệu Dashboard (Tiêu chí D & G):**
  * Sử dụng Postman hoặc Trình duyệt truy cập địa chỉ `GET http://localhost:8005/api/v1/metrics`.
  * Ban đầu, các chỉ số sẽ ở mức 0.
  * Ta thực hiện chạy file `test_integration.py` (hoặc gửi thử tin nhắn giả lập qua MQTT). Trình duyệt F5 tải lại trang `/api/v1/metrics` sẽ hiển thị ngay số liệu được cập nhật tức thời (ví dụ: nhiệt độ trung bình phòng Lab thay đổi, số lượt quẹt thẻ tăng lên, tỷ lệ deny rate cập nhật), chứng minh khả năng thu thập và tổng hợp dữ liệu chính xác.
