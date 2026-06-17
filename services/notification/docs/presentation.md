# Hướng Dẫn Trình Bày Demo — A7: Notification Service

Bản tài liệu này hướng dẫn chi tiết kịch bản thuyết trình và bảo vệ đồ án tích hợp hệ thống cho nhóm phụ trách dịch vụ **Notification Service (A7)** theo quy trình 6 bước chuẩn.

---

## 1. Vai trò của nhóm
* **Tên dịch vụ:** Notification Service (A7).
* **Vai trò trong hệ thống Smart Campus:**
  * Tiếp nhận các yêu cầu gửi thông báo sự cố khẩn cấp từ các dịch vụ quản lý nghiệp vụ.
  * Phân phối tin nhắn cảnh báo đa kênh (SMS, Telegram, Email, Console Log).
  * Đảm bảo thông tin nguy hiểm tiếp cận nhanh nhất tới lực lượng an ninh và ban quản trị trường học.
* **Mô hình giao tiếp:** Hoạt động với vai trò thuần **REST Provider** (cung cấp API dịch vụ đồng bộ).

---

## 2. Input
* **Dữ liệu nhận:** Request JSON đồng bộ qua giao thức HTTP POST chứa yêu cầu thông báo:
  ```json
  {
    "title": "🚨 CẢNH BÁO AN NINH",
    "message": "Phát hiện người lạ đột nhập khu vực Hallway Zone A lúc 02:30:10Z.",
    "severity": "HIGH",
    "channels": ["telegram", "sms"],
    "metadata": {
      "camera_id": "CAM-HALLWAY-01"
    }
  }
  ```
* **Nguồn gửi:** Gửi từ Core Business Service (khi phát hiện sự cố an ninh/an toàn).
* **Giao thức:** REST HTTP POST (Yêu cầu Header xác thực `Authorization: Bearer <AUTH_TOKEN>`).

---

## 3. Xử lý nghiệp vụ
* **Xác thực an toàn:** Kiểm duyệt Token Bearer có khớp với mã bí mật chung `smart-campus-dev-token-2026` hay không. Nếu không khớp, trả về mã lỗi HTTP 401 Unauthorized.
* **Validate dữ liệu:** Kiểm duyệt cấu trúc dữ liệu yêu cầu bằng thư viện Pydantic. Nếu thiếu trường bắt buộc (như thông điệp `message` trống), từ chối và trả về lỗi HTTP 422.
* **Định tuyến tin nhắn đa kênh (Mock Dispatcher):**
  * Tách danh sách `channels` yêu cầu gửi.
  * Đối với kênh `"console"`: Đẩy thông tin cảnh báo định dạng nổi bật ra màn hình console.
  * Đối với kênh `"sms"`: Giả lập đẩy tin nhắn SMS qua API nhà mạng đến số điện thoại khẩn cấp.
  * Đối với kênh `"telegram"`: Giả lập gọi API Bot Telegram để đưa cảnh báo vào nhóm bảo vệ an ninh.
  * Đối với kênh `"email"`: Giả lập gửi thư cảnh báo sự cố đến Email Ban giám hiệu.
* **Lưu nhật ký thông báo:** Lưu trữ bản ghi thông báo vào bộ cơ sở dữ liệu tạm thời trong RAM. Để chống tràn bộ nhớ, hệ thống giới hạn lưu giữ tối đa 1000 tin gần nhất.

---

## 4. Output
* **Dữ liệu trả ra:** Phản hồi JSON (HTTP 201 Created) chứa ID thông báo, danh sách kênh gửi thành công và nhãn trạng thái `"status": "sent"`.
  ```json
  {
    "notification_id": "notif-77777777",
    "status": "sent",
    "channels_sent": ["telegram", "sms"],
    "created_at": "2026-06-17T02:30:10Z"
  }
  ```

---

## 5. Output gửi cho ai?
* **Bên nhận:** Trả trực tiếp trong HTTP Response đồng bộ cho **Core Business Service (A6)**.
* **Môi trường thực tế:** Gửi tín hiệu hiển thị cảnh báo lên hệ thống điều hành thực tế (Telegram Client, SMS Gateway).

---

## 6. Minh chứng demo
* **Container running:** Chạy lệnh `docker compose ps` để kiểm tra container `notification` đang ở trạng thái *Up (healthy)*.
* **Health endpoint:** `GET http://localhost:8007/health` trả về trạng thái ok.
* **Minh chứng nhật ký log đa kênh (Tiêu chí F & G):**
  * Khi Core Business kích hoạt một cuộc gọi gửi cảnh báo an ninh, ta kiểm tra log console của container `notification`. Log sẽ hiển thị chính xác các dòng chữ phân tuyến đa kênh giả lập sinh động:
    `[Auth] Bearer token verified successfully.`
    `[SMS] 💬 Gửi tin nhắn SMS cảnh báo đến Hotline: 0912XXXXXX`
    `[Telegram] 📲 Đã đẩy cảnh báo vào nhóm an ninh bảo vệ qua Telegram API...`
    `[Mail] 📧 Đã gửi thư báo cáo sự cố đến email Ban giám hiệu...`
  * Đồng thời, kiểm tra endpoint xem lại các thông báo gần nhất tại `GET http://localhost:8007/api/v1/notifications/recent` sẽ hiển thị đầy đủ danh sách cảnh báo đã gửi.
