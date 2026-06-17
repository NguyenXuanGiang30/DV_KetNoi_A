"""
A7: Notification Service — Smart Campus
Nhận yêu cầu cảnh báo từ Core Business (cặp 4) và giả lập gửi thông báo đa kênh.
"""

import os
import uuid
import urllib.request
import urllib.parse
import json
import smtplib
from datetime import datetime, timezone
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "smart-campus-dev-token-2026")

def send_telegram_alert(message: str, severity: str, alert_type: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"[{SERVICE_NAME}] ⚠️ Telegram variables not set. Skipping Telegram notification.")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    formatted_msg = (
        f"🚨 *Smart Campus Alert* 🚨\n\n"
        f"🔹 *Type:* `{alert_type}`\n"
        f"🔹 *Severity:* `{severity}`\n"
        f"🔹 *Message:* {message}\n"
        f"🔹 *Time:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": formatted_msg,
        "parse_mode": "Markdown"
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
        
        # Build email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 [Smart Campus] {severity} Alert: {alert_type}"
        msg["From"] = user
        msg["To"] = receiver
        
        text = f"Smart Campus Alert\n\nSeverity: {severity}\nType: {alert_type}\nMessage: {message}\nTime: {datetime.now().isoformat()}"
        html = f"""\
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; padding: 15px; margin-bottom: 20px;">
              <h2 style="color: #721c24; margin-top: 0;">🚨 Smart Campus Alert 🚨</h2>
              <table style="width: 100%; border-collapse: collapse;">
                <tr>
                  <td style="padding: 5px; font-weight: bold; width: 120px;">Alert Type:</td>
                  <td style="padding: 5px; color: #721c24;">{alert_type}</td>
                </tr>
                <tr>
                  <td style="padding: 5px; font-weight: bold;">Severity:</td>
                  <td style="padding: 5px;"><span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; font-weight: bold;">{severity}</span></td>
                </tr>
                <tr>
                  <td style="padding: 5px; font-weight: bold;">Message:</td>
                  <td style="padding: 5px;">{message}</td>
                </tr>
                <tr>
                  <td style="padding: 5px; font-weight: bold;">Timestamp:</td>
                  <td style="padding: 5px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
              </table>
            </div>
            <p style="font-size: 0.8em; color: #666;">This is an automated notification from your Smart Campus system.</p>
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
    """Cặp 4: Core Business gửi yêu cầu cảnh báo."""
    notification_id = f"NOTIF-{uuid.uuid4().hex[:8].upper()}"
    channels = req.channels or ["console"]
    created_at = now_iso()

    # Gửi thông báo qua các kênh
    for channel in channels:
        print(f"[{SERVICE_NAME}] 📢 [{channel.upper()}] [{req.severity}] {req.alert_type}: {req.message}")
        if channel.lower() == "telegram":
            send_telegram_alert(req.message, req.severity, req.alert_type)
        elif channel.lower() == "email":
            send_email_alert(req.message, req.severity, req.alert_type)

    item = {
        "notification_id": notification_id,
        "source_service": req.source_service,
        "alert_type": req.alert_type,
        "severity": req.severity,
        "message": req.message,
        "related_event_id": req.related_event_id,
        "status": "sent",
        "channels_sent": channels,
        "created_at": created_at,
    }
    NOTIFICATIONS.append(item)

    return NotificationResponse(
        notification_id=notification_id,
        status="sent",
        channels_sent=channels,
        created_at=created_at,
    )


@app.get("/api/v1/notifications/recent", dependencies=[Depends(verify_token)])
def get_recent_notifications(limit: int = 20):
    """Lấy danh sách thông báo gần đây."""
    items = NOTIFICATIONS[-limit:]
    items.reverse()
    return {"items": items, "total": len(NOTIFICATIONS)}
