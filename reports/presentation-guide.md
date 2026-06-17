# Hướng Dẫn Trình Bày Demo Tích Hợp Hệ Thống — Smart Campus

Bản tài liệu này hướng dẫn chi tiết kịch bản thuyết trình và bảo vệ đồ án tích hợp hệ thống Smart Campus theo **quy trình 6 bước chuẩn** của giảng viên. Mỗi nhóm/thành viên phụ trách dịch vụ có thể bám sát khung nội dung này để trình bày ngắn gọn, mạch lạc và đạt điểm tối đa.

---

## Mục lục các nhóm (Dịch vụ)
1. [A1: IoT Ingestion Service](#1-a1-iot-ingestion-service)
2. [A2: Camera Stream Service](#2-a2-camera-stream-service)
3. [A3: Access Gate Service](#3-a3-access-gate-service)
4. [A4: AI Vision Service](#4-a4-ai-vision-service)
5. [A5: Analytics Service](#5-a5-analytics-service)
6. [A6: Core Business Service](#6-a6-core-business-service)
7. [A7: Notification Service](#7-a7-notification-service)

---

## 1. A1: IoT Ingestion Service

### 1. Vai trò của nhóm
* **Tên dịch vụ:** IoT Ingestion Service (A1).
* **Vai trò trong Smart Campus:** Tiếp nhận, làm sạch và chuẩn hóa dữ liệu từ các thiết bị cảm biến môi trường (nhiệt độ, độ ẩm, khí CO2, khói) trước khi đưa vào hệ thống xử lý trung tâm.
* **Mô hình:** Hoạt động với vai trò vừa là **Consumer** (nhận tin nhắn raw) vừa là **Publisher** (gửi tin nhắn đã xử lý).

### 2. Input
* **Dữ liệu nhận:** Gói tin JSON thô của cảm biến (chứa thông tin nhiệt độ, độ ẩm, CO2, khói, trạng thái chuyển động).
* **Nguồn gửi:** Thiết bị cảm biến thực tế hoặc simulator giả lập thiết bị phần cứng.
* **Giao thức:** Nhận bất đồng bộ qua MQTT topic: `smart-campus/raw/iot/environment`.

### 3. Xử lý nghiệp vụ
* **Kiểm tra đầu vào:** Kiểm tra cấu trúc JSON, xác minh gói tin có đầy đủ các trường dữ liệu bắt buộc.
* **Validate Whitelist:** Tra cứu `device_id` đối chiếu với danh mục thiết bị hợp lệ được cấu hình trong whitelist file CSV `IoT_device_registry.csv`.
* **Phân loại trạng thái:** Áp dụng logic nghiệp vụ phân loại môi trường:
  * Trạng thái `invalid_device` nếu ID thiết bị lạ.
  * Trạng thái `danger` nếu nhiệt độ $\ge 40^\circ\text{C}$ hoặc CO2 $\ge 1800\,\text{ppm}$ hoặc phát hiện khói $\ge 1.0\,\text{ppm}$ (cảnh báo cháy/độc hại).
  * Trạng thái `warning` nếu nhiệt độ $\ge 35^\circ\text{C}$ hoặc CO2 $\ge 1200\,\text{ppm}$ hoặc pin yếu dưới $20\%$.
  * Trạng thái `normal` cho điều kiện an toàn.

### 4. Output
* **Dữ liệu trả ra:** JSON processed event chứa dữ liệu đo đạc đã chuẩn hóa kèm theo trạng thái phân loại (`status`) và cấp độ cảnh báo (`alert_level`).

### 5. Output gửi cho ai?
* **Điểm gửi:** Publish tin nhắn lên MQTT broker.
* **Topic nhận:** `smart-campus/events/sensor`.
* **Bên nhận tiếp theo (Consumer):** **Core Business (A6)** (để áp dụng chính sách an toàn) và **Analytics (A5)** (để tính toán dashboard).

### 6. Minh chứng demo
* Lệnh kiểm tra container hoạt động: `docker compose ps` (Trạng thái `iot-ingestion` là *Up (healthy)*).
* Endpoint sức khỏe: Truy cập `GET http://localhost:8001/health` phản hồi `status: "ok"` và `mqtt_connected: true`.
* Nhật ký hoạt động: Log console hiển thị quá trình nhận tin nhắn thô, tra cứu whitelist CSV thành công và publish tin nhắn chuẩn hóa.

---

## 2. A2: Camera Stream Service

### 1. Vai trò của nhóm
* **Tên dịch vụ:** Camera Stream Service (A2).
* **Vai trò trong Smart Campus:** Quản lý luồng dữ liệu camera giám sát, phát hiện chuyển động tại hiện trường để kích hoạt nhận diện thông minh, tối ưu băng thông hệ thống.
* **Mô hình:** Hoạt động với vai trò là **REST Client** (gọi AI Vision) và **MQTT Publisher** (gửi kết quả camera).

### 2. Input
* **Dữ liệu nhận:** Luồng video liên tục dạng MJPEG stream.
* **Nguồn gửi:** URL camera cấu hình thông qua biến môi trường `CAMERA_STREAM_URL`.
* **Giao thức:** Đọc luồng qua kết nối HTTP.

### 3. Xử lý nghiệp vụ
* **Đọc & Giải mã hình ảnh:** Tách các khung hình (frame) từ luồng MJPEG với tần suất cấu hình sẵn (ví dụ: 1 frame mỗi 2 giây).
* **Phát hiện chuyển động (Motion Detection):** Áp dụng thuật toán so sánh khác biệt khung hình (frame difference) để đo lường tỷ lệ chuyển động.
* **Áp dụng Cooldown:** Thiết lập thời gian cooldown (ví dụ: 10 giây) để tránh gửi liên tiếp nhiều ảnh của cùng một sự kiện chuyển động.
* **Trí tuệ nhân tạo:** Khi tỷ lệ chuyển động vượt ngưỡng cấu hình, chụp frame ảnh hiện tại gửi sang AI Vision Service qua API REST để nhận diện vật thể.

### 4. Output
* **Dữ liệu trả ra:** JSON event chứa mã camera, trạng thái chuyển động, danh sách vật thể nhận dạng kèm bounding box, và mức độ rủi ro an ninh (`risk_level`).

### 5. Output gửi cho ai?
* **Điểm gửi:** Publish sự kiện lên MQTT broker.
* **Topic nhận:** `smart-campus/events/camera`.
* **Bên nhận tiếp theo (Consumer):** **Analytics (A5)** (thống kê chuyển động) và **Core Business (A6)** (đánh giá nguy cơ an ninh nếu có vật thể lạ/người lạ).

### 6. Minh chứng demo
* Lệnh kiểm tra container hoạt động: `docker compose ps` (Trạng thái `camera-stream` là *Up (healthy)*).
* Endpoint sức khỏe: `GET http://localhost:8002/health` trả về kết quả trạng thái stream và số lượt phát hiện chuyển động.
* Nhật ký hoạt động: Log hiển thị tiến trình bắt khung hình, log gọi thành công API `/detect` của AI Vision kèm theo payload kết quả.

---

## 3. A3: Access Gate Service

### 1. Vai trò của nhóm
* **Tên dịch vụ:** Access Gate Service (A3).
* **Vai trò trong Smart Campus:** Quản lý đóng/mở cửa ra vào phòng học, văn phòng sử dụng thẻ RFID, lưu trữ nhật ký quẹt thẻ.
* **Mô hình:** Hoạt động với vai trò **MQTT Consumer** (nhận quẹt thẻ), **REST Client** (gọi Core), **REST Provider** (cung cấp log) và **MQTT Publisher** (gửi sự kiện cửa).

### 2. Input
* **Dữ liệu nhận:** Gói tin chứa mã thẻ UID sinh viên, ID cổng (`door_id`) và hướng đi (`direction`: in/out).
* **Nguồn gửi:** Đầu đọc thẻ RFID tại cửa.
* **Giao thức:** Nhận qua MQTT topic `smart-campus/raw/access/rfid-uid`.

### 3. Xử lý nghiệp vụ
* **Đối chiếu Whitelist:** Tra cứu UID thẻ trong tệp whitelist CSV `Acessgate_uid_whitelist.csv` được mount vào container.
* **Xác thực chính sách:** Gọi đồng bộ sang Core Business Service qua REST API `POST /access/check` để kiểm tra các luật mở rộng (Ví dụ: sinh viên có lịch học tại phòng đó không, có bị cấm ra vào không, cửa đang mở/khóa...).
* **Dự phòng Fail-Open:** Nếu Core Business bị lỗi/timeout, Access Gate tự động đưa ra quyết định dựa trên whitelist nội bộ của mình để tránh kẹt sinh viên tại cửa.

### 4. Output
* **Dữ liệu trả ra:** JSON quyết định cho phép ra vào (`access_result: granted/denied`) kèm lý do cụ thể và lưu nhật ký quẹt thẻ vào database.

### 5. Output gửi cho ai?
* **Điểm gửi:**
  * Publish sự kiện lên MQTT topic `smart-campus/events/access` cho **Core Business (A6)** và **Analytics (A5)**.
  * Cung cấp REST API `GET /access/logs/recent` cho **Core Business (A6)** đồng bộ log.

### 6. Minh chứng demo
* Lệnh kiểm tra container hoạt động: `docker compose ps` (Trạng thái `access-gate` là *Up (healthy)*).
* Endpoint sức khỏe: `GET http://localhost:8003/health` phản hồi ok.
* Nhật ký hoạt động: Log hiển thị quẹt thẻ UID thành công, quyết định mở cửa (`granted`) hoặc chặn lại (`denied`), và log kích hoạt Fail-Open khi Core Business mất kết nối.

---

## 4. A4: AI Vision Service

### 1. Vai trò của nhóm
* **Tên dịch vụ:** AI Vision Service (A4).
* **Vai trò trong Smart Campus:** Cung cấp lõi xử lý thị giác máy tính thông minh, phân tích ảnh từ camera để tìm vật thể/người lạ và so khớp khuôn mặt ra vào.
* **Mô hình:** Hoạt động với vai trò thuần **REST Provider** (cung cấp API dịch vụ).

### 2. Input
* **Dữ liệu nhận:** 
  * API `/detect`: Ảnh camera (Base64 hoặc URL) kèm mã camera.
  * API `/vision/face-match`: Ảnh khuôn mặt và ID khuôn mặt gốc tham chiếu.
* **Nguồn gửi:** Camera Stream (gọi nhận dạng vật thể) và Core Business (gọi so khớp khuôn mặt).
* **Giao thức:** Gọi qua REST HTTP POST.

### 3. Xử lý nghiệp vụ
* **Xác thực an toàn:** Kiểm tra HTTP Header chứa token bảo mật hợp lệ (`AUTH_TOKEN`).
* **Phân tích hình ảnh (Mock AI Inference):**
  * Sử dụng logic giả lập nhận diện vật thể: Nhận biết nhãn (`person`, `vehicle`, `unknown`), trả ra bounding box chi tiết và tính toán độ tin cậy từ 0.70 - 0.99.
  * Đánh giá mức độ rủi ro của vật thể phát hiện (`risk_level: high` nếu phát hiện phương tiện lạ hoặc người lạ ở khu vực cấm).
  * Thực hiện so sánh vector khuôn mặt và trả về kết quả khớp (`matched: true/false`).

### 4. Output
* **Dữ liệu trả ra:** JSON response chứa mảng các đối tượng nhận diện (`detections`), toạ độ bounding box (`bbox`), độ tin cậy (`confidence`), hoặc cờ trạng thái trùng khớp khuôn mặt.

### 5. Output gửi cho ai?
* **Bên nhận:** Trả trực tiếp trong HTTP Response cho **Camera Stream (A2)** và **Core Business (A6)**.

### 6. Minh chứng demo
* Lệnh kiểm tra container hoạt động: `docker compose ps` (Trạng thái `ai-vision` là *Up (healthy)*).
* Endpoint sức khỏe: `GET http://localhost:8004/health`.
* Xử lý lỗi chuẩn hóa: Thử nghiệm gọi API không truyền token hoặc thiếu ảnh, API trả về mã lỗi `401` / `400` định dạng **Problem Details (RFC 7807)** rất rõ ràng.

---

## 5. A5: Analytics Service

### 1. Vai trò của nhóm
* **Tên dịch vụ:** Analytics Service (A5).
* **Vai trò trong Smart Campus:** Tổng hợp toàn bộ dữ liệu hoạt động của hệ thống, tính toán các chỉ số đo lường hiệu năng (KPIs) thời gian thực phục vụ hiển thị màn hình điều khiển.
* **Mô hình:** Hoạt động với vai trò **MQTT Consumer** (lọc 4 topic) và **REST Provider** (cung cấp dashboard metrics).

### 2. Input
* **Dữ liệu nhận:** Sự kiện môi trường, sự kiện quẹt thẻ ra vào, sự kiện camera an ninh và các cảnh báo khẩn cấp phát ra từ hệ thống.
* **Nguồn gửi:** Publish từ các dịch vụ A1, A2, A3, A6.
* **Giao thức:** Đăng ký nhận tin bất đồng bộ qua 4 topic MQTT trên HiveMQ Cloud.

### 3. Xử lý nghiệp vụ
* **Tổng hợp bộ đếm:** Đọc tin nhắn và cộng dồn số lượng sự kiện theo từng loại.
* **Tính toán trung bình:** Phân nhóm dữ liệu nhiệt độ, độ ẩm theo từng phòng học (`location`) và tính toán nhiệt độ/độ ẩm trung bình tức thời.
* **Tính toán tỷ lệ an ninh:** Đo lường tỷ lệ quẹt thẻ lỗi/từ chối ra vào (`access_deny_rate_percent`).
* **Giám sát thiết bị:** Quản lý danh sách các thiết bị cảm biến sắp hết pin để đề xuất bảo trì.

### 4. Output
* **Dữ liệu trả ra:** JSON chứa toàn bộ các chỉ số thống kê KPIs tổng hợp của hệ thống Smart Campus.

### 5. Output gửi cho ai?
* **Điểm nhận:** Trả về khi có yêu cầu truy vấn REST API tại endpoint `/api/v1/metrics`.
* **Bên nhận tiếp theo:** Giao diện điều khiển Web Dashboard của Ban quản lý hoặc ứng dụng di động giám sát.

### 6. Minh chứng demo
* Lệnh kiểm tra container hoạt động: `docker compose ps` (Trạng thái `analytics` là *Up (healthy)*).
* Endpoint sức khỏe: `GET http://localhost:8005/health`.
* Dữ liệu thực tế: Gọi `GET http://localhost:8005/api/v1/metrics` hiển thị toàn bộ các chỉ số trung bình và tỷ lệ từ chối cửa được tính toán tự động chính xác.

---

## 6. A6: Core Business Service

### 1. Vai trò của nhóm
* **Tên dịch vụ:** Core Business Service (A6).
* **Vai trò trong Smart Campus:** Trung tâm đưa ra quyết định nghiệp vụ (Central Brain). Lắng nghe mọi diễn biến trong hệ thống, đối chiếu với các kịch bản chính sách và kích hoạt phản ứng khẩn cấp (như cảnh báo cháy, cảnh báo đột nhập).
* **Mô hình:** Hoạt động với vai trò **MQTT Consumer** (nhận 3 topic sự kiện), **REST Provider** (check chính sách), **REST Client** (gọi gửi thông báo) và **MQTT Publisher** (phát cảnh báo).

### 2. Input
* **Dữ liệu nhận:** 
  * Sự kiện chuẩn hóa từ cảm biến môi trường, cửa ra vào và camera.
  * REST API: Cổng check quyền ra vào `POST /access/check` từ Access Gate.
* **Nguồn gửi:** Gửi từ A1, A2, A3 qua MQTT broker.
* **Giao thức:** Đăng ký subscribe 3 topic MQTT qua HiveMQ Cloud.

### 3. Xử lý nghiệp vụ
* **Áp dụng luật an toàn (Safety Rule):** Nếu nhận sự kiện cảm biến có `status == "danger"` (cháy, khí độc) $\rightarrow$ tự động kích hoạt trạng thái báo động khẩn cấp.
* **Áp dụng luật an ninh (Security Rule):** Nếu nhận sự kiện quẹt thẻ bị chặn (`denied`) hoặc sự kiện camera phát hiện người lạ (`unknown_person == true`) $\rightarrow$ tự động kích hoạt cảnh báo đột nhập.
* **Khung giờ hoạt động:** Kiểm tra thời gian sự kiện (chỉ cho phép hoạt động ra vào thông thường từ 06:00 đến 22:00).
* **Đồng bộ hóa:** Gọi REST API `/access/logs/recent` của Access Gate để lấy dữ liệu lịch sử quẹt thẻ phục vụ phân tích.

### 4. Output
* **Dữ liệu trả ra:** 
  * JSON cảnh báo hệ thống (`core-alert`) chứa chi tiết sự cố và cấp độ nguy hiểm.
  * Lệnh gọi yêu cầu gửi thông báo khẩn cấp.

### 5. Output gửi cho ai?
* **Điểm gửi:**
  * Publish tin cảnh báo lên MQTT topic `smart-campus/events/core-alert` cho **Analytics (A5)**.
  * Gọi REST API `POST /api/v1/notifications` của **Notification Service (A7)** để phát cảnh báo.

### 6. Minh chứng demo
* Lệnh kiểm tra container hoạt động: `docker compose ps` (Trạng thái `core-business` là *Up (healthy)*).
* Endpoint sức khỏe: `GET http://localhost:8006/health`.
* Nhật ký hoạt động: Log xử lý các sự kiện MQTT, log áp dụng rule phát hiện nguy cơ và tiến trình kích hoạt luồng gửi thông báo cảnh báo khẩn cấp.

---

## 7. A7: Notification Service

### 1. Vai trò của nhóm
* **Tên dịch vụ:** Notification Service (A7).
* **Vai trò trong Smart Campus:** Cổng phát cảnh báo đa phương thức (Console, SMS, Telegram, Email), đảm bảo thông tin sự cố khẩn cấp tiếp cận được đúng người nhận.
* **Mô hình:** Hoạt động với vai trò thuần **REST Provider** (cung cấp API nhận tin nhắn).

### 2. Input
* **Dữ liệu nhận:** JSON request chứa tiêu đề cảnh báo, mô tả chi tiết, mức độ nghiêm trọng và mảng các kênh cần gửi (`channels: ["telegram", "sms", "email"]`).
* **Nguồn gửi:** Core Business (gọi khi phát hiện sự cố nghiệp vụ).
* **Giao thức:** Gọi qua REST HTTP POST.

### 3. Xử lý nghiệp vụ
* **Xác thực:** Kiểm tra Bearer token hợp lệ trong header của yêu cầu gửi đến.
* **Phân tích nghiệp vụ:** Kiểm tra tính hợp lệ của schema bằng Pydantic.
* **Định tuyến tin nhắn:** Định tuyến và giả lập quá trình gửi tin nhắn qua các kênh tương ứng:
  * Đẩy thông báo ra log Console hệ thống.
  * Giả lập gửi SMS tới số hotline an ninh.
  * Giả lập đẩy tin cảnh báo thông qua Telegram Bot API vào nhóm quản trị viên.
  * Giả lập gửi email thông báo sự cố cho Ban giám hiệu.

### 4. Output
* **Dữ liệu trả ra:** JSON response HTTP 201 Created chứa mã ID thông báo, trạng thái gửi (`sent`), danh sách các kênh truyền thành công và thời gian lưu vết.

### 5. Output gửi cho ai?
* **Bên nhận:** Trả kết quả HTTP Response trực tiếp về cho **Core Business (A6)**, đồng thời đẩy log hiển thị kết quả gửi tin thực tế ra console của container.

### 6. Minh chứng demo
* Lệnh kiểm tra container hoạt động: `docker compose ps` (Trạng thái `notification` là *Up (healthy)*).
* Endpoint sức khỏe: `GET http://localhost:8007/health`.
* Nhật ký gửi tin: Log console hiển thị nội dung giả lập:
  * `[Console] 🚨 CẢNH BÁO KHẨN CẤP: Phát hiện khói vượt ngưỡng tại Phòng Lab 102!`
  * `[Telegram] 📲 Đang gửi tin đến nhóm bảo vệ: 'Nhiệt độ phòng máy chủ quá cao!'`
  * `[SMS] 💬 Đã gửi SMS cảnh báo đột nhập tới số 0912xxxxxx`
