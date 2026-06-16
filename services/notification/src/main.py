"""
A7: Notification Service — Smart Campus
Nhận yêu cầu cảnh báo từ Core Business (cặp 4) và giả lập gửi thông báo đa kênh.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "smart-campus-dev-token-2026")

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

    # Giả lập gửi thông báo qua các kênh
    for channel in channels:
        print(f"[{SERVICE_NAME}] 📢 [{channel.upper()}] [{req.severity}] {req.alert_type}: {req.message}")

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
