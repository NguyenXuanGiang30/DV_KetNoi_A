"""
A2: Camera Stream Service — Smart Campus
Đọc MJPEG stream, phát hiện chuyển động, gửi snapshot sang AI Vision,
publish kết quả lên MQTT.
"""

import base64
import json
import os
import ssl
import threading
import time
import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Dict, List, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

SERVICE_NAME = os.getenv("SERVICE_NAME", "camera-stream")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "smart-campus-dev-token-2026")

# ── Camera Config ──
CAMERA_URL = os.getenv("CAMERA_STREAM_URL", "https://camera.labaiotdnu.app/video?key=matkhau_cua_ban")
CAMERA_ID = os.getenv("CAMERA_ID", "cam-gate-a")
CAMERA_LOCATION = os.getenv("CAMERA_LOCATION", "Main Gate A")

# ── AI Vision Config ──
AI_VISION_URL = os.getenv("AI_VISION_URL", "http://ai-vision:8004")

# ── MQTT Config ──
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_IOT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_IOT_PASSWORD", "")
TOPIC_CAMERA = os.getenv("TOPIC_EVENTS_CAMERA", "smart-campus/events/camera")

# ── Motion detection config ──
MOTION_THRESHOLD = float(os.getenv("MOTION_THRESHOLD", "0.50"))
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "10"))
FRAME_INTERVAL = int(os.getenv("FRAME_INTERVAL", "2"))  # Lấy 1 frame mỗi N giây

app = FastAPI(
    title="Smart Campus — Camera Stream Service",
    version=SERVICE_VERSION,
    description="Dịch vụ tiếp nhận và xử lý luồng camera: motion detection, gọi AI Vision.",
)

# ── Storage ──
CAMERA_STATUS = {
    "stream_connected": False,
    "frames_captured": 0,
    "motion_triggers": 0,
    "ai_calls": 0,
    "ai_failures": 0,
    "last_motion": None,
}
DETECTION_HISTORY: List[Dict] = []
mqtt_client_ref = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    time: str
    stream_connected: bool
    motion_triggers: int


def verify_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization or authorization != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Motion Detection (Simplified — không cần OpenCV) ──
def simulate_motion_detection() -> tuple:
    """
    Giả lập phát hiện chuyển động.
    Trong production, sử dụng OpenCV frame difference.
    """
    import random
    motion_detected = random.random() > 0.6  # 40% có motion
    motion_score = round(random.uniform(0.3, 0.95), 2) if motion_detected else round(random.uniform(0.0, 0.3), 2)
    return motion_detected, motion_score


def call_ai_vision(motion_score: float) -> Optional[dict]:
    """Gọi AI Vision để phát hiện vật thể (cặp 1)."""
    try:
        CAMERA_STATUS["ai_calls"] += 1
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                f"{AI_VISION_URL}/detect",
                json={
                    "camera_id": CAMERA_ID,
                    "image_url": f"http://{SERVICE_NAME}/snapshots/{CAMERA_ID}/{int(time.time())}.jpg",
                    "timestamp": now_iso(),
                    "motion_score": motion_score,
                },
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"[{SERVICE_NAME}] ⚠️ AI Vision returned {resp.status_code}")
                CAMERA_STATUS["ai_failures"] += 1
    except httpx.TimeoutException:
        print(f"[{SERVICE_NAME}] ⚠️ AI Vision timeout")
        CAMERA_STATUS["ai_failures"] += 1
    except httpx.RequestError as e:
        print(f"[{SERVICE_NAME}] ⚠️ AI Vision unreachable: {e}")
        CAMERA_STATUS["ai_failures"] += 1
    return None


def publish_camera_event(detection_result: Optional[dict], motion_score: float):
    """Publish kết quả camera event lên MQTT."""
    event = {
        "event_id": f"camera-event-{uuid.uuid4().hex[:8]}",
        "event_type": "camera.vision.processed",
        "source_service": SERVICE_NAME,
        "camera_id": CAMERA_ID,
        "timestamp": now_iso(),
        "location": CAMERA_LOCATION,
        "motion_detected": True,
        "motion_score": motion_score,
    }

    if detection_result:
        event["detections"] = detection_result.get("detections", [])
        event["unknown_person"] = detection_result.get("unknown_person", False)
        event["risk_level"] = detection_result.get("risk_level", "low")
    else:
        event["detections"] = []
        event["unknown_person"] = False
        event["risk_level"] = "low"
        event["ai_status"] = "unavailable"

    DETECTION_HISTORY.append(event)
    if len(DETECTION_HISTORY) > 200:
        del DETECTION_HISTORY[:100]

    if mqtt_client_ref:
        try:
            mqtt_client_ref.publish(TOPIC_CAMERA, json.dumps(event), qos=1)
            print(f"[{SERVICE_NAME}] 📸 Published camera event: motion_score={motion_score}")
        except Exception as e:
            print(f"[{SERVICE_NAME}] ⚠️ MQTT publish failed: {e}")


# ── Camera Processing Loop ──
def camera_processing_loop():
    """Main loop: đọc frame, phát hiện motion, gọi AI Vision."""
    global mqtt_client_ref
    last_trigger = 0

    # Khởi tạo MQTT client
    try:
        from paho.mqtt import client as mqtt_client
        client = mqtt_client.Client(protocol=mqtt_client.MQTTv5)
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        client.connect(MQTT_HOST, MQTT_PORT)
        client.loop_start()
        mqtt_client_ref = client
        print(f"[{SERVICE_NAME}] ✅ MQTT connected for publishing")
    except Exception as e:
        print(f"[{SERVICE_NAME}] ⚠️ MQTT connection failed: {e}")

    CAMERA_STATUS["stream_connected"] = True
    print(f"[{SERVICE_NAME}] 📹 Camera processing loop started (simulated)")

    while True:
        try:
            time.sleep(FRAME_INTERVAL)
            CAMERA_STATUS["frames_captured"] += 1

            motion_detected, motion_score = simulate_motion_detection()

            if motion_detected and motion_score >= MOTION_THRESHOLD:
                now = time.time()
                if now - last_trigger >= COOLDOWN_SECONDS:
                    last_trigger = now
                    CAMERA_STATUS["motion_triggers"] += 1
                    CAMERA_STATUS["last_motion"] = now_iso()

                    print(f"[{SERVICE_NAME}] 🏃 Motion detected! Score: {motion_score}")

                    # Gọi AI Vision
                    result = call_ai_vision(motion_score)
                    publish_camera_event(result, motion_score)
        except Exception as e:
            print(f"[{SERVICE_NAME}] ❌ Loop error: {e}")
            time.sleep(5)


@app.on_event("startup")
async def startup():
    threading.Thread(target=camera_processing_loop, daemon=True).start()
    print(f"[{SERVICE_NAME}] 🚀 Service started")


# ── REST Endpoints ──

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok", service=SERVICE_NAME, version=SERVICE_VERSION,
        time=now_iso(), stream_connected=CAMERA_STATUS["stream_connected"],
        motion_triggers=CAMERA_STATUS["motion_triggers"],
    )


@app.get("/api/v1/camera/status", dependencies=[Depends(verify_token)])
def get_camera_status():
    return CAMERA_STATUS


@app.get("/api/v1/detections/recent", dependencies=[Depends(verify_token)])
def get_recent_detections(limit: int = 20):
    items = list(reversed(DETECTION_HISTORY[-limit:]))
    return {"items": items, "total": len(DETECTION_HISTORY)}
