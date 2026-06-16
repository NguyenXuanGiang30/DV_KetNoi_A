"""
A6: Core Business Service — Smart Campus
Bộ não trung tâm: subscribe MQTT events, áp dụng policy, gọi AI Vision/Gate,
gửi alert cho Notification và Analytics.
"""

import json
import os
import ssl
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

SERVICE_NAME = os.getenv("SERVICE_NAME", "core-business")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "smart-campus-dev-token-2026")

# ── MQTT Config (dùng chung credential IoT để subscribe) ──
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_IOT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_IOT_PASSWORD", "")

TOPIC_SENSOR = os.getenv("TOPIC_EVENTS_SENSOR", "smart-campus/events/sensor")
TOPIC_ACCESS = os.getenv("TOPIC_EVENTS_ACCESS", "smart-campus/events/access")
TOPIC_CAMERA = os.getenv("TOPIC_EVENTS_CAMERA", "smart-campus/events/camera")
TOPIC_CORE_ALERT = os.getenv("TOPIC_EVENTS_CORE_ALERT", "smart-campus/events/core-alert")

# ── Partner URLs ──
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL", "http://notification:8007")
AI_VISION_URL = os.getenv("AI_VISION_URL", "http://ai-vision:8004")
ACCESS_GATE_URL = os.getenv("ACCESS_GATE_URL", "http://access-gate:8003")

app = FastAPI(
    title="Smart Campus — Core Business Service",
    version=SERVICE_VERSION,
    description="Dịch vụ xử lý nghiệp vụ trung tâm: policy engine, alert management.",
)

# ── Storage ──
ALERTS: List[Dict] = []
EVENTS_LOG: List[Dict] = []
MQTT_STATUS = {"connected": False, "message_count": 0}
mqtt_client_ref = None


# ── Models ──
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    time: str
    mqtt_connected: bool
    alerts_count: int


class AccessCheckRequest(BaseModel):
    uid: str
    door_id: str
    direction: str


class AccessCheckResponse(BaseModel):
    decision: str  # ALLOW / DENY
    reason_code: str
    policy_id: Optional[str] = None


# ── Auth ──
def verify_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if authorization != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid bearer token")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Policy Engine ──
def evaluate_sensor_event(event: dict):
    """Đánh giá event cảm biến và tạo alert nếu cần."""
    evt_status = event.get("status", "normal")
    if evt_status in ("danger", "sensor_error", "invalid_device"):
        create_alert(
            alert_type="SENSOR_THRESHOLD_EXCEEDED" if evt_status == "danger" else "SYSTEM_ERROR",
            severity="HIGH" if evt_status == "danger" else "MEDIUM",
            message=f"[{evt_status.upper()}] Device {event.get('device_id')}: {event.get('reason')} "
                    f"(Temp: {event.get('temperature_c')}°C)",
            related_event_id=event.get("event_id"),
        )
    elif evt_status == "warning":
        create_alert(
            alert_type="SENSOR_THRESHOLD_EXCEEDED",
            severity="MEDIUM",
            message=f"[WARNING] Device {event.get('device_id')}: {event.get('reason')}",
            related_event_id=event.get("event_id"),
        )


def evaluate_access_event(event: dict):
    """Đánh giá event ra/vào và tạo alert nếu denied."""
    if event.get("access_result") == "denied":
        create_alert(
            alert_type="UNAUTHORIZED_ACCESS",
            severity="HIGH",
            message=f"Truy cập bị từ chối tại {event.get('location', 'Unknown')}: "
                    f"UID {event.get('uid')} - {event.get('reason')}",
            related_event_id=event.get("event_id"),
        )


def evaluate_camera_event(event: dict):
    """Đánh giá event camera."""
    if event.get("unknown_person"):
        create_alert(
            alert_type="UNKNOWN_PERSON",
            severity="HIGH",
            message=f"Phát hiện người lạ tại {event.get('location', 'Unknown')} "
                    f"(confidence: {event.get('motion_score', 'N/A')})",
            related_event_id=event.get("event_id"),
        )


def create_alert(alert_type: str, severity: str, message: str, related_event_id: str = None):
    """Tạo alert, publish lên MQTT và gửi cho Notification."""
    alert_id = f"ALERT-{uuid.uuid4().hex[:8].upper()}"
    alert = {
        "id": alert_id,
        "source_service": SERVICE_NAME,
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "related_event_id": related_event_id,
        "status": "OPEN",
        "created_at": now_iso(),
        "resolved_at": None,
    }
    ALERTS.append(alert)
    print(f"[{SERVICE_NAME}] 🚨 Alert created: [{severity}] {alert_type}: {message}")

    # Publish alert event trên MQTT (cặp 8: Core → Analytics)
    if mqtt_client_ref:
        try:
            mqtt_client_ref.publish(TOPIC_CORE_ALERT, json.dumps(alert), qos=1)
        except Exception as e:
            print(f"[{SERVICE_NAME}] ⚠️ Failed to publish alert to MQTT: {e}")

    # Gửi notification (cặp 4: Core → Notification)
    send_notification_async(alert)


def send_notification_async(alert: dict):
    """Gửi cảnh báo cho Notification Service (fire-and-forget)."""
    def _send():
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(
                    f"{NOTIFICATION_URL}/api/v1/notifications",
                    json={
                        "source_service": SERVICE_NAME,
                        "alert_type": alert["alert_type"],
                        "severity": alert["severity"],
                        "message": alert["message"],
                        "related_event_id": alert.get("related_event_id"),
                        "channels": ["console", "telegram"],
                    },
                    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                )
                if resp.status_code == 201:
                    print(f"[{SERVICE_NAME}] ✅ Notification sent: {resp.json().get('notification_id')}")
                else:
                    print(f"[{SERVICE_NAME}] ⚠️ Notification response: {resp.status_code}")
        except Exception as e:
            print(f"[{SERVICE_NAME}] ⚠️ Notification failed: {e}")

    threading.Thread(target=_send, daemon=True).start()


# ── MQTT Client ──
def start_mqtt_client():
    global mqtt_client_ref
    try:
        from paho.mqtt import client as mqtt_client

        def on_connect(client, userdata, flags, reason_code, properties=None):
            MQTT_STATUS["connected"] = True
            print(f"[{SERVICE_NAME}] ✅ Connected to HiveMQ")
            for topic in [TOPIC_SENSOR, TOPIC_ACCESS, TOPIC_CAMERA]:
                client.subscribe(topic, qos=1)
                print(f"[{SERVICE_NAME}] 📡 Subscribed: {topic}")

        def on_disconnect(client, userdata, flags, reason_code, properties=None):
            MQTT_STATUS["connected"] = False

        def on_message(client, userdata, message):
            try:
                event = json.loads(message.payload.decode())
                MQTT_STATUS["message_count"] += 1
                EVENTS_LOG.append({"topic": message.topic, "event": event, "received_at": now_iso()})

                if message.topic == TOPIC_SENSOR:
                    evaluate_sensor_event(event)
                elif message.topic == TOPIC_ACCESS:
                    evaluate_access_event(event)
                elif message.topic == TOPIC_CAMERA:
                    evaluate_camera_event(event)
            except Exception as e:
                print(f"[{SERVICE_NAME}] ❌ Error: {e}")

        client = mqtt_client.Client(protocol=mqtt_client.MQTTv5)
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        mqtt_client_ref = client

        client.connect(MQTT_HOST, MQTT_PORT)
        client.loop_forever()
    except Exception as e:
        print(f"[{SERVICE_NAME}] ❌ MQTT failed: {e}")


@app.on_event("startup")
async def startup():
    threading.Thread(target=start_mqtt_client, daemon=True).start()
    print(f"[{SERVICE_NAME}] 🚀 Service started")


# ── REST Endpoints ──

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok", service=SERVICE_NAME, version=SERVICE_VERSION,
        time=now_iso(), mqtt_connected=MQTT_STATUS["connected"],
        alerts_count=len(ALERTS),
    )


@app.post("/access/check", response_model=AccessCheckResponse, dependencies=[Depends(verify_token)])
def access_check(req: AccessCheckRequest):
    """Cặp 10: Access Gate gọi — kiểm tra policy ra/vào."""
    # Ví dụ policy đơn giản: cho phép tất cả trong giờ hành chính
    current_hour = datetime.now().hour
    if 6 <= current_hour <= 22:
        return AccessCheckResponse(decision="ALLOW", reason_code="within_allowed_hours", policy_id="POL-001")
    else:
        return AccessCheckResponse(decision="DENY", reason_code="outside_allowed_hours", policy_id="POL-002")


@app.get("/api/v1/alerts/recent", dependencies=[Depends(verify_token)])
def get_recent_alerts(limit: int = 20):
    """Lấy danh sách cảnh báo gần đây."""
    items = list(reversed(ALERTS[-limit:]))
    return {"items": items, "total": len(ALERTS)}


@app.get("/api/v1/alerts/{alert_id}", dependencies=[Depends(verify_token)])
def get_alert_by_id(alert_id: str):
    for alert in ALERTS:
        if alert["id"] == alert_id:
            return alert
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


@app.get("/api/v1/events/log", dependencies=[Depends(verify_token)])
def get_events_log(limit: int = 50):
    """Xem log tất cả event đã nhận."""
    items = list(reversed(EVENTS_LOG[-limit:]))
    return {"items": items, "total": len(EVENTS_LOG)}
