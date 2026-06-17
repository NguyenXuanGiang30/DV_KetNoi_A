# Hướng Dẫn Trình Bày Demo — A3: Access Gate Service

Bản tài liệu này hướng dẫn chi tiết kịch bản thuyết trình và bảo vệ đồ án tích hợp hệ thống cho nhóm phụ trách dịch vụ **Access Gate Service (A3)** theo quy trình 6 bước chuẩn.

---

## 1. Vai trò của nhóm
* **Tên dịch vụ:** Access Gate Service (A3).
* **Vai trò trong hệ thống Smart Campus:**
  * Kiểm soát cửa ra vào các phòng học, phòng chức năng dựa trên thẻ RFID.
  * Tự động kiểm tra quyền hạn thẻ đối chiếu với whitelist cục bộ và luật nghiệp vụ của Core Business.
  * Lưu trữ nhật ký (log) các lượt quẹt thẻ phục vụ việc kiểm tra và báo cáo.
* **Mô hình giao tiếp:** Đóng vai trò là **MQTT Consumer** (nhận tin quẹt thẻ thô), **REST Client** (gọi Core Business check chính sách), **REST Provider** (cung cấp API truy vấn log), và **MQTT Publisher** (phát sự kiện xử lý cửa).

---

## 2. Input
* **Dữ liệu nhận:**
  * **Event nhận (MQTT):** Tin nhắn chứa thông tin quẹt thẻ RFID thô:
    ```json
    {
      "event_id": "rfid-raw-11111",
      "event_type": "access.rfid.raw",
      "timestamp": "2026-06-17T02:30:10Z",
      "uid": "STUDENT_CARD_99",
      "door_id": "DOOR-LAB102",
      "direction": "in"
    }
    ```
  * **API nhận (REST Provider):** Nhận request đồng bộ từ Core Business yêu cầu xem lịch sử ra vào gần đây qua endpoint `GET /access/logs/recent`.
* **Nguồn gửi:** Đầu đọc thẻ RFID đặt tại các cửa ra vào trong khuôn viên.
* **Giao thức:** Nhận bất đồng bộ qua MQTT topic `smart-campus/raw/access/rfid-uid` và đồng bộ qua REST HTTP.

---

## 3. Xử lý nghiệp vụ
* **Định dạng dữ liệu:** Kiểm tra tính hợp lệ của gói tin đầu vào.
* **Tra cứu Whitelist cục bộ:** Đọc danh sách thẻ được cấp phép từ file CSV `/app/data/Acessgate_uid_whitelist.csv`. Nếu UID trùng khớp $\rightarrow$ Kết quả sơ bộ: Cho phép (`granted`), lý do: `uid_matched`. Nếu không khớp $\rightarrow$ Chặn lại (`denied`), lý do: `uid_not_found`.
* **Gọi kiểm tra Core Policy (REST Client):** Gửi thông tin quẹt thẻ lên dịch vụ Core Business qua API `POST /access/check` kèm mã token bảo mật để kiểm tra luật thời gian ra vào mở rộng.
* **Cơ chế dự phòng Fail-Open:** 
  * Cuộc gọi REST check policy được giới hạn thời gian chờ `timeout=5.0` giây và nằm trong khối bắt lỗi ngoại lệ `try...except`.
  * Nếu Core Business bị sập hoặc mất kết nối, Access Gate sẽ ghi log cảnh báo và **áp dụng ngay kết quả đối chiếu whitelist cục bộ** để ra quyết định đóng/mở cửa, tránh trường hợp sinh viên bị kẹt ngoài cửa khi máy chủ trung tâm gặp sự cố.

---

## 4. Output
* **Dữ liệu trả ra:**
  * **Publish MQTT:** Sự kiện cửa đã xử lý (Access Event) chứa thông tin sinh viên (nếu thuộc whitelist) và kết quả quyết định (`granted` / `denied`).
    ```json
    {
      "event_id": "access-proc-22222",
      "event_type": "access.swipe.processed",
      "source_service": "access-gate",
      "timestamp": "2026-06-17T02:30:10Z",
      "raw_event_id": "rfid-raw-11111",
      "uid": "STUDENT_CARD_99",
      "student_id": "DNU-12345",
      "full_name": "Nguyen Xuan Giang",
      "class_name": "K26-CNTT",
      "door_id": "DOOR-LAB102",
      "location": "Lab room 102",
      "direction": "in",
      "access_result": "granted",
      "reason": "uid_matched"
    }
    ```
  * **REST Response:** Trả về danh sách log lịch sử quẹt thẻ gần đây cho Core Business hoặc các dịch vụ quản lý khác truy xuất.

---

## 5. Output gửi cho ai?
* **MQTT:** Publish sự kiện lên topic `smart-campus/events/access`.
  * Bên nhận tiếp theo (Consumer): **Core Business (A6)** (để kiểm tra xem có quẹt thẻ lỗi liên tục không) và **Analytics (A5)** (để thống kê tỷ lệ ra vào).
* **REST:** Trả kết quả HTTP Response trực tiếp về cho **Core Business (A6)** khi Core Business truy vấn endpoint `GET /access/logs/recent`.

---

## 6. Minh chứng demo
* **Container running:** Chạy lệnh `docker compose ps` để kiểm tra container `access-gate` đang chạy ổn định.
* **Health endpoint:** Truy cập `GET http://localhost:8003/health` trả về trạng thái service và kết nối MQTT (HTTP 200 OK).
* **Nhật ký log nghiệp vụ:** Log hiển thị chi tiết:
  `[MQTT-Sub] RFID Swipe detected: UID STUDENT_CARD_99 at DOOR-LAB102`
  `[Process] Matching UID with Acessgate_uid_whitelist.csv... Found Student: Nguyen Xuan Giang`
  `[REST-Client] Verifying policy with Core Business at /access/check... Policy approved.`
  `[Process] Final Decision: GRANTED (Reason: uid_matched)`
  `[MQTT-Pub] Publishing event to smart-campus/events/access`
* **Demo kịch bản Fail-Open (Tiêu chí F):** Tắt tạm thời container `core-business`. Thực hiện quẹt một thẻ hợp lệ trong whitelist. Log của `access-gate` sẽ cảnh báo `⚠️ Core Business policy check failed: ... Falling back to local whitelist decision` và cửa vẫn được mở (`granted`), chứng minh cơ chế tự phục hồi hoạt động đúng thiết kế.
