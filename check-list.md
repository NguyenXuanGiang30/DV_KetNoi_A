# Check-list Service Notification — Smart Campus

## Mục tiêu
Tài liệu này kiểm tra lại tiêu chí A-H cho service `notification` và giải thích rõ:
- Service làm gì
- Endpoint /health hoạt động
- Contract đã có
- Payload đúng schema
- Xử lý lỗi / timeout
- Minh chứng demo rõ ràng

---

## Tổng quan đánh giá A-H
| Mã | Tiêu chí | Trạng thái | Ghi chú |
|---|---|---|---|
| A | Nghiệp vụ rõ ràng | Hoàn thành | Service nhận alert từ core-business và mô phỏng gửi cảnh báo. |
| B | Service chạy Docker Compose | Hoàn thành | Container `smart-campus-notification` chạy và healthy. |
| C | Endpoint /health hoạt động | Hoàn thành | `GET /health` trả về 200 OK. |
| D | Tích hợp đúng contract | Hoàn thành | OpenAPI contract có mặt trong `services/notification/contracts/notification.openapi.yaml`. |
| E | Payload đúng schema | Hoàn thành | Đã định nghĩa request/response model và schema. |
| F | Xử lý lỗi / timeout | Hoàn thành | Xử lý token, severity, channels và trả lỗi rõ. |
| G | Minh chứng đầy đủ | Hoàn thành | Build + run + health check đã thực hiện. |
| H | Trình bày demo rõ ràng | Hoàn thành | Hướng dẫn demo và lưu ý PowerShell đã có. |

> Ghi chú: phần gửi thật SMS/Email/Telegram hiện đang mô phỏng qua log. Nếu cần tối ưu hơn, đây là phần cần bổ sung.

---

## A. Nghiệp vụ rõ ràng (1.0)
- Service `notification` là dịch vụ cảnh báo đa kênh cho hệ thống Smart Campus.
- Input: nhận POST từ `core-business` tại `/api/v1/notifications`.
- Xử lý: xác thực token, kiểm tra dữ liệu đầu vào, mô phỏng gửi cảnh báo qua các kênh.
- Output: trả về `notification_id`, `status`, `channels_sent`, `created_at`.

> Giải thích: service này phục vụ nhiệm vụ cảnh báo của hệ thống, không phải là dịch vụ thu thập dữ liệu. Nó nhận alert từ `core-business` và thực hiện bước gửi thông báo.

---

## B. Service chạy ổn định bằng Docker Compose (1.5)
- Đã build thành công Docker image cho service `notification`.
- Đã chạy thành công container `smart-campus-notification` qua Docker Compose.
- Container ở trạng thái `healthy`.

> Giải thích: Docker Compose sử dụng `services.notification` trong `docker-compose.yml`, chạy port nội bộ 8000 và expose ra 8007.

---

## C. Endpoint /health hoạt động (1.0)
- `GET /health` trả về `200 OK`.
- Response mẫu:
```json
{"status":"ok","service":"notification","version":"1.0.0","time":"2026-06-17T19:54:34+00:00"}
```
- Kiểm tra thực tế bằng PowerShell đã thành công.

> Giải thích: endpoint này dùng để nhóm demo hoặc đối tác gọi nhanh kiểm tra service có chạy được không.

---

## D. Tích hợp đúng contract với nhóm khác (2.0)
- OpenAPI contract nằm ở `services/notification/contracts/notification.openapi.yaml`.
- Contract mô tả:
  - `GET /health`
  - `POST /api/v1/notifications`
  - `GET /api/v1/notifications/recent`
- Contract cũng định nghĩa `securitySchemes` bearer token.

> Giải thích: đây là phần contract để nhóm khác dùng khi gọi REST API. Service `core-business` có thể gọi theo schema này.

---

## E. Payload / request đúng schema (1.0)
- Request schema `NotificationRequest` yêu cầu:
  - `source_service` (string)
  - `alert_type` (string)
  - `severity` (string)
  - `message` (string)
- Optional:
  - `related_event_id`
  - `channels`
  - `recipients`
- Response schema `NotificationResponse` trả về:
  - `notification_id`
  - `status`
  - `channels_sent`
  - `created_at`

> Giải thích: schema hiện tại yêu cầu các trường quan trọng và hỗ trợ mở rộng cho nhiều kênh.

---

## F. Có xử lý lỗi / timeout (1.0)
- Service xử lý lỗi cụ thể:
  - Thiếu `Authorization` -> 401 Unauthorized.
  - Token không hợp lệ -> 401 Unauthorized.
  - `severity` không nằm trong `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` -> 422.
  - `channels` chứa giá trị không hợp lệ -> 422.
- Error response có cấu trúc giải thích rõ lý do.

> Giải thích: service không crash khi nhận request sai, mà trả về lỗi rõ ràng để nhóm gọi biết sửa.

---

## G. Minh chứng đầy đủ (1.5)
- Đã có các bằng chứng sau:
  - `docker compose build notification` thành công.
  - `docker compose up -d notification` thành công.
  - Container `smart-campus-notification` chạy và healthy.
  - `curl http://localhost:8007/health` thực tế trả về 200.
- Nên bổ sung file `check-list.md` để lưu lại evidence các bước.

> Giải thích: Đây là minh chứng để giám sát nghiệm thu, log và endpoint hoạt động.

---

## H. Trình bày demo rõ ràng (1.0)
- Các bước demo rõ ràng:
  1. Copy `.env.example` thành `.env`.
  2. Chạy `docker compose up -d --build` hoặc `docker compose up -d notification`.
  3. Kiểm tra `/health`.
  4. Gọi POST `/api/v1/notifications` với bearer token.
- Nếu chạy PowerShell và thấy warning `Script Execution Risk`, dùng `curl.exe` hoặc `Invoke-WebRequest -UseBasicParsing`.

> Giải thích: demo phải rõ đầu vào, xử lý, đầu ra, và cách test thực tế.

---

## Những phần còn thiếu / cần chú ý
- Hiện tại service `notification` chưa tích hợp gửi thực tế đến SMS/Email/Telegram.
  - Nó đang mô phỏng đa kênh bằng `print()` console.
  - Nếu cần thực tế, cần thêm module gửi SMS/Email/Telegram và cấu hình credential tương ứng.
- `recipients` được hỗ trợ ở schema nhưng hiện vẫn chỉ là thông tin lưu và không dùng để gửi thực tế.
- Nếu muốn hoàn chỉnh hơn, nên bổ sung:
  - `POST /api/v1/notifications` thực sự gửi qua API của Telegram.
  - `POST /api/v1/notifications` gửi email hoặc SMS.

---

## Các câu hỏi thường gặp và trả lời

### 1. Service `notification` gửi đa kênh thật không?
Hiện tại chưa gửi thật. Nó mô phỏng gửi bằng log console để đảm bảo luồng cảnh báo đã đúng và vẫn có thể mở rộng sau này.

### 2. Tại sao cần token `Authorization`?
Service dùng token bearer để bảo vệ endpoint POST cảnh báo, tránh người lạ gửi alert giả mạo.

### 3. Nếu dùng `curl` trên PowerShell mà báo warning thì nên làm sao?
Dùng `curl.exe http://localhost:8007/health` hoặc `Invoke-WebRequest -Uri 'http://localhost:8007/health' -UseBasicParsing`.

### 4. Tại sao `recipients` vẫn optional?
Vì hiện service có thể gửi cảnh báo chung qua kênh console hoặc tự động gửi đến danh sách mặc định. `recipients` sau này dùng khi chuyển sang gửi thực tế Email/SMS/Telegram.

---

## Kết luận
Service `notification` đã đáp ứng tốt các tiêu chí A-H về mặt chức năng và deploy.
Phần cần bổ sung nếu muốn hoàn chỉnh hơn là tích hợp gửi SMS/Email/Telegram thật sự.
http://localhost:8007/health
http://localhost:8007/docs#/default/get_recent_notifications_api_v1_notifications_recent_get