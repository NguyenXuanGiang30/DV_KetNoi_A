import os
import uuid
import urllib.request
import urllib.parse
import urllib.error
import json
import smtplib
import ssl
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "smart-campus-dev-token-2026")

# ── MQTT Config ──
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_IOT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_IOT_PASSWORD", "")
TOPIC_CORE_ALERT = os.getenv("TOPIC_EVENTS_CORE_ALERT", "smart-campus/events/core-alert")

# ── Deduplication Cache ──
PROCESSED_ALERTS = {}  # Key: alert_id, Value: timestamp (float)

def send_telegram_alert(message: str, severity: str, alert_type: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"[{SERVICE_NAME}] ⚠️ Telegram variables not set. Skipping Telegram notification.")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Map severity to friendly Vietnamese status and emoji
    severity_map = {
        "CRITICAL": "🔴 NGUY HIỂM (Khẩn cấp)",
        "HIGH": "🟠 CAO (Cần cảnh giác)",
        "MEDIUM": "🟡 TRUNG BÌNH (Cần lưu ý)",
        "LOW": "🟢 THẤP (Thông tin)"
    }
    sev_friendly = severity_map.get(severity.upper(), severity)
    
    # Map type to friendly name
    type_map = {
        "SENSOR_THRESHOLD_EXCEEDED": "Vượt ngưỡng cảm biến 🌡️",
        "UNAUTHORIZED_ACCESS": "Xâm nhập không hợp lệ ❌",
        "SYSTEM_ERROR": "Lỗi hệ thống ⚠️"
    }
    type_friendly = type_map.get(alert_type.upper(), alert_type)

    formatted_msg = (
        f"🚨 <b>CẢNH BÁO SMART CAMPUS</b> 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>Mức độ:</b> {sev_friendly}\n"
        f"📌 <b>Sự kiện:</b> {type_friendly}\n"
        f"📝 <b>Nội dung:</b> {message}\n"
        f"⏰ <b>Thời gian:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Hệ thống giám sát tự động.</i>"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": formatted_msg,
        "parse_mode": "HTML"
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res = response.read().decode("utf-8")
            print(f"[{SERVICE_NAME}] ✅ Telegram alert sent: {res[:50]}...")
            return True
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8") if e.fp else str(e)
        print(f"[{SERVICE_NAME}] ❌ Failed to send Telegram alert: HTTP {e.code} - {err_msg}")
        return False
    except Exception as e:
        print(f"[{SERVICE_NAME}] ❌ Failed to send Telegram alert: {e}")
        return False

def send_email_alert(message: str, severity: str, alert_type: str) -> bool:
    host = os.getenv("SMTP_HOST")
    port_str = os.getenv("SMTP_PORT", "587")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    receiver = os.getenv("SMTP_RECEIVER")
    
    if not all([host, user, password, receiver]):
        print(f"[{SERVICE_NAME}] ⚠️ SMTP credentials not fully set. Skipping Email notification.")
        return False
        
    try:
        port = int(port_str)
        
        # Map severity to friendly Vietnamese status and emoji
        severity_map = {
            "CRITICAL": "🔴 NGUY HIỂM (Khẩn cấp)",
            "HIGH": "🟠 CAO (Cần cảnh giác)",
            "MEDIUM": "🟡 TRUNG BÌNH (Cần lưu ý)",
            "LOW": "🟢 THẤP (Thông tin)"
        }
        sev_friendly = severity_map.get(severity.upper(), severity)
        
        # Map type to friendly name
        type_map = {
            "SENSOR_THRESHOLD_EXCEEDED": "Vượt ngưỡng cảm biến 🌡️",
            "UNAUTHORIZED_ACCESS": "Xâm nhập không hợp lệ ❌",
            "SYSTEM_ERROR": "Lỗi hệ thống ⚠️"
        }
        type_friendly = type_map.get(alert_type.upper(), alert_type)

        severity_colors = {
            "CRITICAL": "#dc3545",  # Red
            "HIGH": "#fd7e14",      # Orange
            "MEDIUM": "#ffc107",    # Yellow
            "LOW": "#28a745"        # Green
        }
        border_color = severity_colors.get(severity.upper(), "#6c757d")
        
        severity_bg = {
            "CRITICAL": "#f8d7da",
            "HIGH": "#fff3cd",
            "MEDIUM": "#fffdf0",
            "LOW": "#d4edda"
        }
        bg_color = severity_bg.get(severity.upper(), "#f8f9fa")
        
        severity_text_color = {
            "CRITICAL": "#721c24",
            "HIGH": "#856404",
            "MEDIUM": "#664d03",
            "LOW": "#155724"
        }
        text_color = severity_text_color.get(severity.upper(), "#383d41")

        # Build email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 [Smart Campus] Cảnh báo {sev_friendly} - {type_friendly}"
        msg["From"] = user
        msg["To"] = receiver
        
        text = f"Cảnh báo Smart Campus\nMức độ: {sev_friendly}\nSự kiện: {type_friendly}\nNội dung: {message}\nThời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        html = f"""\
        <html>
          <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f4f6f9; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-top: 5px solid {border_color};">
              <div style="background-color: {border_color}; padding: 20px; text-align: center;">
                <h2 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: bold; letter-spacing: 0.5px;">🚨 CẢNH BÁO SMART CAMPUS</h2>
              </div>
              
              <div style="padding: 25px; background-color: {bg_color}; color: {text_color};">
                <table style="width: 100%; border-collapse: collapse;">
                  <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                    <td style="padding: 12px 0; font-weight: bold; width: 150px; font-size: 15px;">⚠️ Mức độ cảnh báo:</td>
                    <td style="padding: 12px 0; font-size: 15px;"><span style="background-color: {border_color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{sev_friendly}</span></td>
                  </tr>
                  <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                    <td style="padding: 12px 0; font-weight: bold; font-size: 15px;">📌 Loại sự kiện:</td>
                    <td style="padding: 12px 0; font-size: 15px; font-weight: bold;">{type_friendly}</td>
                  </tr>
                  <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                    <td style="padding: 12px 0; font-weight: bold; font-size: 15px;">📝 Nội dung chi tiết:</td>
                    <td style="padding: 12px 0; font-size: 15px; line-height: 1.5;">{message}</td>
                  </tr>
                  <tr>
                    <td style="padding: 12px 0; font-weight: bold; font-size: 15px;">⏰ Thời gian phát hiện:</td>
                    <td style="padding: 12px 0; font-size: 15px;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</td>
                  </tr>
                </table>
              </div>
              
              <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #6c757d; border-top: 1px solid #e9ecef;">
                <p style="margin: 0; font-weight: bold;">Hệ thống giám sát tự động Smart Campus</p>
                <p style="margin: 4px 0 0 0;">Vui lòng không phản hồi trực tiếp email tự động này.</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        
        # Connect and send
        server = smtplib.SMTP(host, port, timeout=5)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, receiver, msg.as_string())
        server.quit()
        print(f"[{SERVICE_NAME}] ✅ Email alert sent successfully to {receiver}")
        return True
    except Exception as e:
        print(f"[{SERVICE_NAME}] ❌ Failed to send Email alert: {e}")
        return False


app = FastAPI(
    title="Smart Campus — Notification Service",
    version=SERVICE_VERSION,
    description="Dịch vụ gửi cảnh báo đa kênh (SMS, Email, Telegram) cho hệ thống Smart Campus.",
)

# ── In-memory storage ──
NOTIFICATIONS: List[Dict] = []


# ── Models ──
class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str
    time: str


class NotificationRequest(BaseModel):
    source_service: str = Field(..., min_length=2, examples=["core-business"])
    alert_type: str = Field(..., examples=["SENSOR_THRESHOLD_EXCEEDED"])
    severity: str = Field(..., examples=["HIGH"])
    message: str = Field(..., min_length=5, examples=["Nhiệt độ phòng Lab A101 vượt ngưỡng 40°C"])
    related_event_id: Optional[str] = None
    channels: Optional[List[str]] = Field(default=None, examples=[["console", "telegram"]])
    recipients: Optional[List[str]] = None


class NotificationResponse(BaseModel):
    notification_id: str
    status: str  # sent, queued, failed
    channels_sent: List[str]
    created_at: str


class NotificationItem(BaseModel):
    notification_id: str
    source_service: str
    alert_type: str
    severity: str
    message: str
    status: str
    channels_sent: List[str]
    created_at: str


# ── Auth ──
def verify_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "https://smart-campus.local/problems/unauthorized",
                    "title": "Unauthorized", "status": 401,
                    "detail": "Missing Authorization header"},
        )
    expected = f"Bearer {AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "https://smart-campus.local/problems/unauthorized",
                    "title": "Unauthorized", "status": 401,
                    "detail": "Invalid bearer token"},
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Unified Logic: process_alert_event ──
def process_alert_event(alert: dict):
    """Xử lý cảnh báo nhận được từ Core Business (MQTT hoặc REST), áp dụng routing và retry."""
    alert_id = alert.get("id")
    message = alert.get("message", "")
    severity = str(alert.get("severity", "LOW")).upper()
    alert_type = alert.get("alert_type", "UNKNOWN")
    source_service = alert.get("source_service", "core-business")
    related_event_id = alert.get("related_event_id")

    # 1. Chống gửi trùng (Deduplication)
    if alert_id:
        now = time.time()
        if alert_id in PROCESSED_ALERTS and (now - PROCESSED_ALERTS[alert_id]) < 60.0:
            print(f"[{SERVICE_NAME}] 🔄 Alert {alert_id} already processed. Skipping notification.")
            return
        PROCESSED_ALERTS[alert_id] = now

    # 2. Routing theo severity
    channels = []
    recipients = []
    if severity == "CRITICAL":
        channels = ["telegram", "email"]
        recipients = ["all"]
    elif severity == "HIGH":
        channels = ["telegram"]
        recipients = ["security_team"]
    elif severity == "MEDIUM":
        channels = ["email"]
        recipients = ["admin"]
    else:  # LOW / other
        channels = ["console"]
        recipients = ["log"]

    # 3. Gửi thông báo có retry (Exponential Backoff)
    success_channels = []
    failed_channels = []

    for channel in channels:
        print(f"[{SERVICE_NAME}] 📢 Sending [{severity}] alert via {channel.upper()} (recipients: {recipients})")
        if channel == "console":
            print(f"[{SERVICE_NAME}] 💻 [LOG ONLY] {message}")
            success_channels.append("console")
        elif channel == "telegram":
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            if not token or not chat_id:
                print(f"[{SERVICE_NAME}] ⚠️ Telegram variables not set. Skipping Telegram notification.")
                failed_channels.append("telegram")
            else:
                # Retry up to 3 times (attempts: 0, 1, 2)
                sent = False
                for attempt in range(3):
                    if send_telegram_alert(message, severity, alert_type):
                        sent = True
                        break
                    # Tránh dừng luồng chính quá lâu nếu lỗi, nhưng vẫn đảm bảo backoff
                    backoff_time = 2 ** attempt
                    print(f"[{SERVICE_NAME}] ⚠️ Telegram attempt {attempt+1} failed. Retrying in {backoff_time}s...")
                    time.sleep(backoff_time)
                if sent:
                    success_channels.append("telegram")
                else:
                    failed_channels.append("telegram")
        elif channel == "email":
            host = os.getenv("SMTP_HOST")
            user = os.getenv("SMTP_USER")
            password = os.getenv("SMTP_PASSWORD")
            receiver = os.getenv("SMTP_RECEIVER")
            if not all([host, user, password, receiver]):
                print(f"[{SERVICE_NAME}] ⚠️ SMTP credentials not fully set. Skipping Email notification.")
                failed_channels.append("email")
            else:
                # Retry up to 3 times
                sent = False
                for attempt in range(3):
                    if send_email_alert(message, severity, alert_type):
                        sent = True
                        break
                    backoff_time = 2 ** attempt
                    print(f"[{SERVICE_NAME}] ⚠️ Email attempt {attempt+1} failed. Retrying in {backoff_time}s...")
                    time.sleep(backoff_time)
                if sent:
                    success_channels.append("email")
                else:
                    failed_channels.append("email")

    notification_id = f"NOTIF-{uuid.uuid4().hex[:8].upper()}"
    status_str = "sent" if len(success_channels) > 0 else "failed"

    item = {
        "notification_id": notification_id,
        "source_service": source_service,
        "alert_id": alert_id,
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "related_event_id": related_event_id,
        "status": status_str,
        "channels_sent": success_channels,
        "channels_failed": failed_channels,
        "created_at": now_iso(),
    }
    NOTIFICATIONS.append(item)
    print(f"[{SERVICE_NAME}] 📝 Logged notification {notification_id} - status: {status_str.upper()}")


# ── MQTT Client ──
def start_mqtt_client():
    """Khởi động MQTT client và subscribe topic cảnh báo từ Core Business."""
    try:
        from paho.mqtt import client as mqtt_client
        
        def on_connect(client, userdata, flags, reason_code, properties=None):
            print(f"[{SERVICE_NAME}] ✅ Connected to HiveMQ Broker: {reason_code}")
            client.subscribe(TOPIC_CORE_ALERT, qos=1)
            print(f"[{SERVICE_NAME}] 📡 Subscribed to topic: {TOPIC_CORE_ALERT}")
            
        def on_disconnect(client, userdata, flags, reason_code, properties=None):
            print(f"[{SERVICE_NAME}] ⚠️ Disconnected from HiveMQ Broker: {reason_code}")
            
        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                print(f"[{SERVICE_NAME}] 📩 Received alert via MQTT: {payload.get('id')}")
                process_alert_event(payload)
            except Exception as e:
                print(f"[{SERVICE_NAME}] ❌ Error processing MQTT alert: {e}")

        client = mqtt_client.Client(protocol=mqtt_client.MQTTv5)
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        
        client.connect(MQTT_HOST, MQTT_PORT)
        client.loop_forever()
    except Exception as e:
        print(f"[{SERVICE_NAME}] ❌ MQTT Client start failed: {e}")


@app.on_event("startup")
async def startup_event():
    threading.Thread(target=start_mqtt_client, daemon=True).start()
    print(f"[{SERVICE_NAME}] 🚀 Startup event: MQTT Listener started.")


# ── Endpoints ──

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok", service=SERVICE_NAME, version=SERVICE_VERSION, time=now_iso()
    )


@app.post(
    "/api/v1/notifications",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_token)],
)
def create_notification(req: NotificationRequest):
    """Cặp 4: Core Business gửi yêu cầu cảnh báo qua REST (hoặc test script)."""
    # Gửi qua quy trình routing & retry & deduplication thống nhất
    alert_payload = {
        "id": req.related_event_id or f"REST-{uuid.uuid4().hex[:8].upper()}",
        "source_service": req.source_service,
        "alert_type": req.alert_type,
        "severity": req.severity,
        "message": req.message,
        "related_event_id": req.related_event_id,
    }
    process_alert_event(alert_payload)
    
    # Lấy notification vừa tạo ở cuối list
    latest = NOTIFICATIONS[-1] if NOTIFICATIONS else {}
    return NotificationResponse(
        notification_id=latest.get("notification_id", "UNKNOWN"),
        status=latest.get("status", "sent"),
        channels_sent=latest.get("channels_sent", []),
        created_at=latest.get("created_at", now_iso()),
    )


@app.get("/api/v1/notifications/recent", dependencies=[Depends(verify_token)])
def get_recent_notifications(limit: int = 20):
    """Lấy danh sách thông báo gần đây."""
    items = NOTIFICATIONS[-limit:]
    items.reverse()
    return {"items": items, "total": len(NOTIFICATIONS)}
