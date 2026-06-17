# Đánh giá tiêu chí chấm điểm — A3: Access Gate Service

Bản tài liệu này tự đánh giá và đối chiếu dịch vụ **A3: Access Gate Service** với thang điểm và tiêu chí chấm điểm tích hợp hệ thống.

## Bảng tổng hợp kết quả

| Mã | Tiêu chí | Điểm tối đa | Trạng thái | Điểm tự đánh giá | Minh chứng & Vị trí trong dự án |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **A** | Nghiệp vụ rõ ràng | 1.0 | ✅ Đạt | 1.0 | Vai trò Publisher & REST Provider. Tài liệu tại [event-contract-access.md](file:///d:/BTL_DV_KetNoi/services/access_gate/docs/event-contract-access.md). |
| **B** | Chạy ổn định bằng Docker Compose | 1.5 | ✅ Đạt | 1.5 | Khai báo service `access-gate` trong `docker-compose.yml`, mount volume chứa whitelist và có healthcheck. |
| **C** | Endpoint `/health` hoạt động | 1.0 | ✅ Đạt | 1.0 | API `GET /health` trả về HTTP 200 OK. |
| **D** | Tích hợp đúng contract với nhóm khác | 2.0 | ✅ Đạt | 2.0 | Tích hợp MQTT bất đồng bộ và cung cấp REST API cho Core Business thành công. |
| **E** | Payload / request đúng schema | 1.0 | ✅ Đạt | 1.0 | Đúng cấu trúc JSON schema của các sự kiện quẹt thẻ đã thống nhất. |
| **F** | Có xử lý lỗi / timeout | 1.0 | ✅ Đạt | 1.0 | Cơ chế kiểm tra policy với Core Business có thiết lập timeout và dự phòng Fail-Open. |
| **G** | Minh chứng đầy đủ | 1.5 | ✅ Đạt | 1.5 | Đầy đủ hình ảnh và log tại thư mục `reports/`. |
| **H** | Trình bày demo rõ ràng | 1.0 | ✅ Đạt | 1.0 | Sử dụng kịch bản test tích hợp của `test_integration.py` làm demo luồng dữ liệu. |
| | **TỔNG CỘNG** | **10.0** | | **10.0/10.0** | |

---

## Chi tiết thực hiện theo từng tiêu chí

### Tiêu chí A: Nghiệp vụ rõ ràng (1.0đ)
- **Vai trò:** Kiểm soát quyền ra vào thông qua quẹt thẻ RFID. Nhận UID thẻ từ broker, đối chiếu danh sách sinh viên được cấp phép, gọi kiểm tra chính sách bổ sung từ Core Business và lưu trữ nhật ký phục vụ truy vấn.
- **Input (Đầu vào):** Sự kiện quẹt thẻ raw nhận từ MQTT topic `smart-campus/raw/access/rfid-uid` hoặc REST API.
- **Xử lý (Logic chính):**
  * Tải whitelist thẻ sinh viên từ file `Datas/Acessgate_uid_whitelist.csv` qua volume mount `/app/data/Acessgate_uid_whitelist.csv`.
  * Đối chiếu UID thẻ: Nếu có trong whitelist, tạm thời ghi nhận trạng thái `granted` (lý do: `uid_matched`); nếu không có, ghi nhận `denied` (lý do: `uid_not_found`).
  * Gọi dịch vụ Core Business thông qua API `POST /access/check` (với Header token hợp lệ) để kiểm tra các luật thời gian/chính sách ra vào mở rộng.
- **Output (Đầu ra):**
  * Publish sự kiện đã xử lý lên MQTT topic `smart-campus/events/access`.
  * Cung cấp các API REST cho Core Business truy xuất: Lịch sử quẹt thẻ (`GET /access/logs/recent`), chi tiết thẻ (`GET /cards/{card_uid}`), trạng thái cổng (`GET /gates/{gate_id}/status`).
- **Tài liệu tham chiếu:**
  * OpenAPI Spec: `services/access_gate/contracts/access-gate.openapi.yaml`
  * Event Contract: `services/access_gate/docs/event-contract-access.md`

### Tiêu chí B: Service chạy ổn định bằng Docker Compose (1.5đ)
- Khai báo dưới dạng service `access-gate` trong `docker-compose.yml`.
- **Volume Mount:**
  ```yaml
  volumes:
    - ./Datas:/app/data
  ```
  Giúp nạp whitelist động từ thư mục dữ liệu dùng chung mà không cần build lại Docker image.
- Tự kiểm tra sức khỏe bằng script `HEALTHCHECK` kiểm tra endpoint `/health` nội bộ.

### Tiêu chí C: Endpoint `/health` hoạt động (1.0đ)
- Endpoint triển khai tại: `GET /health` (Port `8003` ánh xạ vào container port `8000`).
- Phản hồi mẫu (HTTP 200 OK):
  ```json
  {
    "status": "ok",
    "service": "access-gate",
    "version": "1.0.0",
    "time": "2026-06-17T02:30:10Z",
    "mqtt_connected": true,
    "message_count": 8
  }
  ```
- Minh chứng đã lưu tại `reports/health-local.png`.

### Tiêu chí D: Tích hợp đúng contract với nhóm khác (2.0đ)
- Dịch vụ thực hiện kết nối đồng bộ và bất đồng bộ:
  * **REST Provider:** Cung cấp tài nguyên log cho Core Business gọi qua REST: `Core Business (A6)` $\xrightarrow{\text{GET /access/logs/recent}}$ `Access Gate (A3)`.
  * **REST Client:** Gọi xác minh chính sách: `Access Gate (A3)` $\xrightarrow{\text{POST /access/check}}$ `Core Business (A6)`.
  * **MQTT Publisher:** Gửi sự kiện xử lý: `Access Gate (A3)` $\xrightarrow{\text{MQTT: smart-campus/events/access}}$ `Core Business (A6)` và `Analytics (A5)`.
- Đã kiểm thử tích hợp tự động qua file `test_integration.py`.

### Tiêu chí E: Payload / request đúng schema (1.0đ)
- Payload truyền nhận tuân thủ nghiêm ngặt định dạng JSON đã cam kết.
- Sử dụng mô hình Pydantic validate dữ liệu cho tất cả các endpoint REST API trong file `services/access_gate/src/main.py`.

### Tiêu chí F: Có xử lý lỗi / timeout (1.0đ)
- **Cơ chế timeout:** Thiết lập timeout tối đa là 5.0 giây khi gọi API `POST /access/check` của Core Business thông qua thư viện `httpx`.
- **Cơ chế Fail-Open & Bắt lỗi:**
  * Quá trình kiểm tra chính sách với Core Business được đặt trong khối `try...except`. Nếu dịch vụ Core Business bị timeout, ngắt mạng hoặc trả về lỗi 5xx, Access Gate sẽ ghi log cảnh báo `⚠️ Core Business policy check failed` và **sử dụng kết quả whitelist cục bộ** (Fail-Open) để phản hồi người dùng ra vào, tránh việc kẹt cửa khi máy chủ trung tâm gặp sự cố.
  * Tự động khôi phục kết nối MQTT khi xảy ra ngắt quãng mạng.

### Tiêu chí G: Minh chứng đầy đủ (1.5đ)
- Các minh chứng đã chuẩn bị trong thư mục `reports/` gồm:
  * Danh sách container chạy ổn định: `reports/docker-compose-ps.png`
  * Nhật ký log thực tế: `reports/logs-compose.txt`
  * Sẵn sàng tích hợp: `reports/readiness-checklist.md`

### Tiêu chí H: Trình bày demo rõ ràng (1.0đ)
- **Luồng dữ liệu của service:**
  `MQTT smart-campus/raw/access/rfid-uid` $\rightarrow$ **[Đối chiếu Whitelist & Gọi Core check policy]** $\rightarrow$ `MQTT smart-campus/events/access`
- Quá trình chạy thử demo được tự động hóa tại mục `3.2` trong script kiểm thử tích hợp `test_integration.py`.
