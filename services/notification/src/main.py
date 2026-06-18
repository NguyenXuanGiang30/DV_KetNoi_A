"""
A7: Notification Service — Smart Campus
Nhận yêu cầu cảnh báo từ Core Business (cặp 4) và gửi thông báo đa kênh.
Kênh gửi: Console, Telegram, Email, SMS, Dashboard
"""

import os
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from dashboard_storage import DashboardStorage
from telegram_sender import send_telegram
from email_sender import send_email
from sms_sender import send_sms

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "smart-campus-dev-token-2026")

app = FastAPI(
    title="Smart Campus — Notification Service",
    version=SERVICE_VERSION,
    description="Dịch vụ gửi cảnh báo đa kênh (Console, Telegram, Email, SMS, Dashboard) cho hệ thống Smart Campus.",
)

# ── In-memory storage ──
NOTIFICATIONS: List[Dict] = []
ALLOWED_CHANNELS = {"console", "telegram", "email", "sms", "dashboard"}
ALLOWED_SEVERITY = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


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
    channels: Optional[List[str]] = Field(default=None, examples=[["console", "email", "telegram", "sms"]])
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


class DashboardNotificationItem(BaseModel):
    notification_id: str
    alert_type: str
    severity: str
    message: str
    source_service: str
    channels_sent: List[str]
    created_at: str
    read: bool
    acknowledged: bool


class NotificationStatsResponse(BaseModel):
    total_notifications: int
    unread_count: int
    unacknowledged_count: int
    severity_distribution: Dict[str, int]


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


# ── Helper Functions ──
async def send_to_channels(
    notification_id: str,
    alert_type: str,
    severity: str,
    message: str,
    source_service: str,
    channels: List[str],
    related_event_id: Optional[str] = None,
    recipients: Optional[List[str]] = None,
):
    """
    Gửi thông báo đến các kênh được chỉ định.
    """
    tasks = []

    for channel in channels:
        if channel == "console":
            severity_emoji = {
                "LOW": "🔵",
                "MEDIUM": "🟡",
                "HIGH": "🔴",
                "CRITICAL": "⛔",
            }.get(severity, "ℹ️")
            print(f"[{SERVICE_NAME}] {severity_emoji} [{channel.upper()}] [{severity}] {alert_type}: {message} (ID: {notification_id})")

        elif channel == "telegram":
            tasks.append(
                send_telegram(
                    notification_id=notification_id,
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    source_service=source_service,
                    related_event_id=related_event_id,
                )
            )

        elif channel == "email":
            tasks.append(
                send_email(
                    notification_id=notification_id,
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    source_service=source_service,
                    related_event_id=related_event_id,
                    recipients=recipients,
                )
            )

        elif channel == "sms":
            tasks.append(
                send_sms(
                    notification_id=notification_id,
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    source_service=source_service,
                    related_event_id=related_event_id,
                    recipients=recipients,
                )
            )

        elif channel == "dashboard":
            DashboardStorage.save_notification(
                notification_id=notification_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                source_service=source_service,
                related_event_id=related_event_id,
                channels_sent=channels,
            )

    # Chạy các task bất đồng bộ
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


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
async def create_notification(
    req: NotificationRequest,
    background_tasks: BackgroundTasks
):
    """
    Cặp 4: Core Business gửi yêu cầu cảnh báo.
    Hệ thống sẽ gửi thông báo đến các kênh được chỉ định.
    """
    # Validate severity
    if req.severity.upper() not in ALLOWED_SEVERITY:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "https://smart-campus.local/problems/invalid-severity",
                "title": "Invalid severity",
                "status": 422,
                "detail": f"Severity must be one of {sorted(ALLOWED_SEVERITY)}",
            },
        )

    # Validate channels
    channels = req.channels or ["console", "dashboard"]
    invalid_channels = [c for c in channels if c not in ALLOWED_CHANNELS]
    if invalid_channels:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "https://smart-campus.local/problems/invalid-channels",
                "title": "Invalid channels",
                "status": 422,
                "detail": f"Allowed channels are {sorted(ALLOWED_CHANNELS)}. Invalid: {invalid_channels}",
            },
        )

    notification_id = f"NOTIF-{uuid.uuid4().hex[:8].upper()}"
    created_at = now_iso()

    # Gửi thông báo trong background
    background_tasks.add_task(
        send_to_channels,
        notification_id=notification_id,
        alert_type=req.alert_type,
        severity=req.severity,
        message=req.message,
        source_service=req.source_service,
        channels=channels,
        related_event_id=req.related_event_id,
        recipients=req.recipients,
    )

    # Lưu vào storage chính
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
    """Lấy danh sách thông báo gần đây từ service."""
    items = NOTIFICATIONS[-limit:]
    items.reverse()
    return {"items": items, "total": len(NOTIFICATIONS)}


@app.get(
    "/api/v1/dashboard/notifications",
    dependencies=[Depends(verify_token)]
)
def get_dashboard_notifications(limit: int = 20):
    """Lấy danh sách thông báo từ dashboard (dành cho UI)."""
    items = DashboardStorage.get_recent_notifications(limit=limit)
    return {"items": items, "total": len(items)}


@app.get(
    "/api/v1/dashboard/statistics",
    response_model=NotificationStatsResponse,
    dependencies=[Depends(verify_token)]
)
def get_dashboard_statistics():
    """Lấy thống kê thông báo trên dashboard."""
    stats = DashboardStorage.get_statistics()
    return NotificationStatsResponse(**stats)


@app.post(
    "/api/v1/dashboard/notifications/{notification_id}/read",
    dependencies=[Depends(verify_token)]
)
def mark_notification_as_read(notification_id: str):
    """Đánh dấu thông báo là đã đọc."""
    success = DashboardStorage.mark_as_read(notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"title": "Notification not found", "status": 404}
        )
    return {"status": "read", "notification_id": notification_id}


@app.post(
    "/api/v1/dashboard/notifications/{notification_id}/acknowledge",
    dependencies=[Depends(verify_token)]
)
def acknowledge_notification(notification_id: str):
    """Xác nhận thông báo (nhân viên đã xử lý)."""
    success = DashboardStorage.acknowledge_notification(notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"title": "Notification not found", "status": 404}
        )
    return {"status": "acknowledged", "notification_id": notification_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8007)),
    )
