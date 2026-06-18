# 🚀 Quick Start — Notification Service

## Bước 1: Chuẩn Bị

### Copy `.env.example` → `.env`
```bash
cp .env.example .env
```

### (Tuỳ chọn) Cấu Hình Telegram
Nếu muốn gửi Telegram thực:
1. Tạo bot trên [@BotFather](https://t.me/botfather)
2. Lấy **Bot Token** và **Chat ID**
3. Cập nhật `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your-actual-token
   TELEGRAM_CHAT_ID=your-actual-chat-id
   ```

### (Tuỳ chọn) Cấu Hình Email SMTP
Nếu muốn gửi Email thực (Gmail example):
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO_LIST=admin@company.com;user@company.com
```

---

## Bước 2: Chạy Service

### Option A: Cục Bộ (Local Development)

```bash
# 1. Đi vào thư mục notification
cd services/notification

# 2. Tạo virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# hoặc
venv\Scripts\activate     # Windows

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Chạy service
cd src
uvicorn main:app --reload --port 8007
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8007
INFO:     Application startup complete
```

### Option B: Docker Compose (Recommended)

```bash
# Từ root directory
docker-compose up notification
```

---

## Bước 3: Test Service

### 1. Health Check
```bash
curl http://localhost:8007/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "notification",
  "version": "1.0.0",
  "time": "2026-06-18T10:30:00+00:00"
}
```

### 2. Gửi Notification Test
```bash
curl -X POST http://localhost:8007/api/v1/notifications \
  -H "Authorization: Bearer smart-campus-dev-token-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "source_service": "core-business",
    "alert_type": "TEST_ALERT",
    "severity": "HIGH",
    "message": "Test notification to all channels",
    "channels": ["console", "email", "telegram", "sms", "dashboard"]
  }'
```

**Response:**
```json
{
  "notification_id": "NOTIF-A1B2C3D4",
  "status": "sent",
  "channels_sent": ["console", "email", "telegram", "sms", "dashboard"],
  "created_at": "2026-06-18T10:30:00+00:00"
}
```

### 3. Xem Dashboard Notifications
```bash
curl http://localhost:8007/api/v1/dashboard/notifications?limit=10 \
  -H "Authorization: Bearer smart-campus-dev-token-2026"
```

### 4. Xem Statistics
```bash
curl http://localhost:8007/api/v1/dashboard/statistics \
  -H "Authorization: Bearer smart-campus-dev-token-2026"
```

---

## Bước 4: Tích Hợp Với Core Business Service

Trong `core-business` service, gửi notification sau khi phát hiện sự kiện:

```python
import requests

def send_alert_to_notification(alert_type: str, severity: str, message: str):
    """
    Gửi cảnh báo đến Notification Service
    """
    notification_url = "http://notification:8000/api/v1/notifications"
    
    payload = {
        "source_service": "core-business",
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "channels": ["console", "email", "telegram", "sms", "dashboard"],
        "recipients": ["admin@smart-campus.local"]
    }
    
    headers = {
        "Authorization": "Bearer smart-campus-dev-token-2026",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(notification_url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        notification_id = response.json()["notification_id"]
        print(f"✅ Notification sent: {notification_id}")
        return notification_id
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")
        return None


# Example: Khi phát hiện threshold
if temperature > THRESHOLD:
    send_alert_to_notification(
        alert_type="SENSOR_THRESHOLD_EXCEEDED",
        severity="HIGH",
        message=f"Nhiệt độ Lab A101 vượt ngưỡng {THRESHOLD}°C (Hiện tại: {temperature}°C)"
    )
```

---

## 📊 Các Kênh Gửi

| Kênh      | Trạng Thái | Mock? | Cấu Hình |
|-----------|-----------|-------|---------|
| Console   | ✅ Ready | Không | N/A |
| Dashboard | ✅ Ready | Không | N/A |
| Telegram  | ✅ Ready | Có | TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID |
| Email     | ✅ Ready | Có | SMTP_* |
| SMS       | ✅ Ready | Có | SMS_* |

**Mock Mode:** Thông báo được in ra console thay vì gửi thực tế.

---

## 🐛 Troubleshooting

### Service không start?
```bash
# Check logs
docker-compose logs notification

# Check requirements installed
pip list | grep fastapi

# Verify port không bị dùng
lsof -i :8007  # macOS/Linux
netstat -ano | findstr :8007  # Windows
```

### Notification không gửi?
1. Kiểm tra Authorization header có token hợp lệ không
2. Xem logs: `docker-compose logs notification`
3. Kiểm tra channels được specify có trong ALLOWED_CHANNELS không
4. Nếu Telegram/Email, kiểm tra `.env` config

### Email/Telegram không hoạt động?
- **Email:** SMTP server hay port sai → Check `.env` SMTP_SERVER, SMTP_PORT
- **Telegram:** Bot token hoặc chat ID sai → Check `.env` TELEGRAM_*

---

## 📚 Tài Liệu Thêm

- **Đầy Đủ Documentation:** [NOTIFICATION_README.md](services/notification/NOTIFICATION_README.md)
- **Implementation Details:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **API Postman Collection:** [notification.postman_collection.json](services/notification/postman/collections/notification.postman_collection.json)

---

## ✅ Checklist

- [ ] Clone repository và vào thư mục project
- [ ] Copy `.env.example` → `.env`
- [ ] (Tuỳ chọn) Cấu hình Telegram/Email
- [ ] Chạy `docker-compose up notification`
- [ ] Test `/health` endpoint
- [ ] Test POST `/api/v1/notifications`
- [ ] Xem notifications trên dashboard
- [ ] Tích hợp vào Core Business Service
- [ ] Kiểm tra logs khi có lỗi

---

**Ready to go! 🚀**
