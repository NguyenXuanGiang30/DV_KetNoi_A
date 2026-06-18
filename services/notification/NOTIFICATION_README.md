# Notification Service — Smart Campus

**Phiên bản:** 1.0.0  
**Port:** 8007  
**Mô tả:** Dịch vụ gửi cảnh báo đa kênh từ Core Business Service

## 📋 Tổng Quan

Notification Service nhận yêu cầu cảnh báo từ Core Business (Cặp 4) và gửi thông báo đến nhiều kênh khác nhau:

- 🖥️ **Console** — In thông báo ra terminal/logs
- 📨 **Email** — Gửi email với định dạng HTML
- 📱 **Telegram** — Gửi tin nhắn tới bot Telegram
- 💬 **SMS** — Gửi tin nhắn SMS (mock mode)
- 📊 **Dashboard** — Lưu thông báo để hiển thị trên dashboard

## 🏗️ Kiến Trúc

```
Core Business Service
        ↓
        ↓ POST /api/v1/notifications
        ↓
Notification Service
        ├→ Console Sender
        ├→ Telegram Sender
        ├→ Email Sender
        ├→ SMS Sender
        └→ Dashboard Storage
```

## 🔧 Cấu Hình

### 1. Telegram Bot

**Để gửi thông báo qua Telegram:**

1. Tạo bot mới trên Telegram qua [@BotFather](https://t.me/botfather)
2. Lấy **Bot Token** từ BotFather
3. Gửi tin nhắn cho bot của bạn
4. Lấy **Chat ID** bằng cách gọi: `https://api.telegram.org/bot{TOKEN}/getUpdates`
5. Cập nhật `.env`:

```bash
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_CHAT_ID=your-chat-id-here
```

**Ở môi trường dev/demo:** Sử dụng `mock-token-123456` và bot sẽ in thông báo ra console.

### 2. Email

**Để gửi thông báo qua Email:**

- **Localhost (Mock):** SMTP Server sẽ in thông báo ra console
  ```bash
  SMTP_SERVER=localhost
  SMTP_PORT=1025
  ```

- **SMTP thực tế (Gmail, SendGrid, v.v.):**
  ```bash
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USERNAME=your-email@gmail.com
  SMTP_PASSWORD=your-app-password
  EMAIL_FROM=your-email@gmail.com
  EMAIL_TO_LIST=recipient@example.com;admin@company.com
  ```

### 3. SMS

**Ở hiện tại:** SMS Service ở **mock mode** — sẽ in thông báo ra console.

**Để gửi SMS thực tế:** Cập nhật `sms_sender.py` để tích hợp với nhà cung cấp SMS (Twilio, Nexmo, v.v.)

```python
# Các biến cấu hình
SMS_PROVIDER=twilio  # hoặc nexmo
SMS_API_KEY=your-api-key
PHONE_NUMBERS=+84903000000;+84904000001
```

## 📡 API Endpoints

### 1. Gửi Thông Báo (Từ Core Business)

```http
POST /api/v1/notifications
Authorization: Bearer smart-campus-dev-token-2026
Content-Type: application/json

{
  "source_service": "core-business",
  "alert_type": "SENSOR_THRESHOLD_EXCEEDED",
  "severity": "HIGH",
  "message": "Nhiệt độ phòng Lab A101 vượt ngưỡng 40°C",
  "related_event_id": "EVENT-12345678",
  "channels": ["console", "email", "telegram", "sms", "dashboard"],
  "recipients": ["admin@smart-campus.local", "+84903000000"]
}
```

**Response (201 Created):**
```json
{
  "notification_id": "NOTIF-A1B2C3D4",
  "status": "sent",
  "channels_sent": ["console", "email", "telegram", "sms", "dashboard"],
  "created_at": "2026-06-18T10:30:00+00:00"
}
```

### 2. Lấy Thông Báo Gần Đây

```http
GET /api/v1/notifications/recent?limit=20
Authorization: Bearer smart-campus-dev-token-2026
```

### 3. Lấy Thông Báo từ Dashboard

```http
GET /api/v1/dashboard/notifications?limit=20
Authorization: Bearer smart-campus-dev-token-2026
```

**Response:**
```json
{
  "items": [
    {
      "notification_id": "NOTIF-A1B2C3D4",
      "alert_type": "SENSOR_THRESHOLD_EXCEEDED",
      "severity": "HIGH",
      "message": "Nhiệt độ phòng Lab A101 vượt ngưỡng 40°C",
      "source_service": "core-business",
      "channels_sent": ["console", "email", "telegram"],
      "created_at": "2026-06-18T10:30:00+00:00",
      "read": false,
      "acknowledged": false
    }
  ],
  "total": 1
}
```

### 4. Lấy Thống Kê Thông Báo

```http
GET /api/v1/dashboard/statistics
Authorization: Bearer smart-campus-dev-token-2026
```

**Response:**
```json
{
  "total_notifications": 150,
  "unread_count": 12,
  "unacknowledged_count": 8,
  "severity_distribution": {
    "LOW": 30,
    "MEDIUM": 50,
    "HIGH": 60,
    "CRITICAL": 10
  }
}
```

### 5. Đánh Dấu Thông Báo Đã Đọc

```http
POST /api/v1/dashboard/notifications/{notification_id}/read
Authorization: Bearer smart-campus-dev-token-2026
```

### 6. Xác Nhận Thông Báo (Đã Xử Lý)

```http
POST /api/v1/dashboard/notifications/{notification_id}/acknowledge
Authorization: Bearer smart-campus-dev-token-2026
```

## 🚀 Chạy Service

### Cục Bộ (Không Docker)

```bash
cd services/notification
python -m venv venv
source venv/bin/activate  # hoặc venv\Scripts\activate (Windows)
pip install -r requirements.txt
export PYTHONPATH=/path/to/src
cd src
uvicorn main:app --reload --port 8007
```

### Docker

```bash
# Build image
docker build -t smart-campus-notification services/notification

# Run container
docker run -p 8007:8000 \
  -e AUTH_TOKEN=your-token \
  -e TELEGRAM_BOT_TOKEN=your-token \
  smart-campus-notification
```

### Docker Compose

```bash
docker-compose up notification
```

## 📝 Severity Levels

| Mức độ    | Emoji | Ý Nghĩa |
|----------|-------|---------|
| LOW      | 🔵   | Thông báo thông thường |
| MEDIUM   | 🟡   | Cảnh báo trung bình |
| HIGH     | 🔴   | Cảnh báo cao |
| CRITICAL | ⛔   | Cảnh báo nghiêm trọng |

## 📚 Dự Tính Phát Triển (v2.0+)

- [ ] Database lưu thông báo (PostgreSQL/MongoDB)
- [ ] Webhook notifications
- [ ] WhatsApp integration
- [ ] Slack integration
- [ ] Message scheduling
- [ ] Notification templates
- [ ] Retry logic & dead letter queue
- [ ] Rate limiting

## 🔐 Bảo Mật

- Tất cả endpoints (trừ `/health`) yêu cầu **Bearer Token** trong header `Authorization`
- Token mặc định: `smart-campus-dev-token-2026` (chỉ cho dev/demo)
- **Production:** Thay đổi token và sử dụng environment variables

## 📞 Hỗ Trợ

Nếu gặp sự cố:
1. Kiểm tra logs: `docker-compose logs notification`
2. Kiểm tra cấu hình `.env`
3. Đảm bảo Core Business Service gửi request đúng format
4. Kiểm tra authentication token
