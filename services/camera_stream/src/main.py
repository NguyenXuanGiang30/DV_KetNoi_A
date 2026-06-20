"""
A2: Camera Stream Service — Smart Campus
Đọc MJPEG stream, phát hiện chuyển động, gửi snapshot sang AI Vision,
publish kết quả lên MQTT.
"""

import base64
import cv2
import json
import numpy as np
import os
import ssl
import threading
import time
import urllib.request
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
MOTION_THRESHOLD = float(os.getenv("MOTION_THRESHOLD", "0.05")) # Ngưỡng nhạy hơn cho pixel thay đổi (5%)
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "10"))
FRAME_INTERVAL = int(os.getenv("FRAME_INTERVAL", "2"))  # Lấy 1 frame mỗi N giây khi ở chế độ fallback

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


def detect_motion(prev_frame, curr_frame) -> tuple:
    """Tính toán sự thay đổi giữa 2 frame để phát hiện chuyển động."""
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)
    
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.GaussianBlur(curr_gray, (21, 21), 0)
    
    # Tính độ lệch tuyệt đối
    diff = cv2.absdiff(prev_gray, curr_gray)
    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    
    # Tính tỷ lệ pixel thay đổi
    non_zero = np.count_nonzero(thresh)
    total_pixels = thresh.shape[0] * thresh.shape[1]
    motion_score = round(non_zero / total_pixels, 2)
    
    return motion_score >= MOTION_THRESHOLD, motion_score


def call_ai_vision(frame: np.ndarray, motion_score: float, request_id: str) -> Optional[dict]:
    """Gọi AI Vision để phát hiện vật thể qua Base64 (cặp 1), hỗ trợ retry tối đa 2 lần (tổng 3 lần thử)."""
    CAMERA_STATUS["ai_calls"] += 1
    
    # Encode frame sang JPG
    _, buffer = cv2.imencode('.jpg', frame)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{AI_VISION_URL}/detect",
                    json={
                        "request_id": request_id,
                        "camera_id": CAMERA_ID,
                        "image_base64": img_base64,
                        "timestamp": now_iso(),
                        "motion_score": motion_score,
                    },
                    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    print(f"[{SERVICE_NAME}] ⚠️ AI Vision returned {resp.status_code} (Attempt {attempt+1}/{max_attempts})")
        except httpx.TimeoutException:
            print(f"[{SERVICE_NAME}] ⚠️ AI Vision timeout (Attempt {attempt+1}/{max_attempts})")
        except httpx.RequestError as e:
            print(f"[{SERVICE_NAME}] ⚠️ AI Vision unreachable: {e} (Attempt {attempt+1}/{max_attempts})")
        
        if attempt < max_attempts - 1:
            time.sleep(1.0) # Wait 1s before retrying

    CAMERA_STATUS["ai_failures"] += 1
    return None


def publish_camera_event(detection_result: Optional[dict], motion_score: float, request_id: str):
    """Publish kết quả camera event lên MQTT."""
    event = {
        "event_id": f"camera-event-{uuid.uuid4().hex[:8]}",
        "request_id": request_id,
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
        event["request_id"] = detection_result.get("request_id", request_id)
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


def fallback_camera_loop():
    """Vòng lặp giả lập dự phòng nếu không mở được webcam/IP camera."""
    import random
    last_trigger = 0
    while True:
        try:
            time.sleep(FRAME_INTERVAL)
            CAMERA_STATUS["frames_captured"] += 1
            motion_detected = random.random() > 0.6
            motion_score = round(random.uniform(0.3, 0.95), 2) if motion_detected else round(random.uniform(0.0, 0.3), 2)

            if motion_detected and motion_score >= 0.50:
                now = time.time()
                if now - last_trigger >= COOLDOWN_SECONDS:
                    last_trigger = now
                    CAMERA_STATUS["motion_triggers"] += 1
                    CAMERA_STATUS["last_motion"] = now_iso()
                    print(f"[{SERVICE_NAME}] 🏃 (Fallback) Motion detected! Score: {motion_score}")
                    
                    # Tạo ảnh đen giả lập khi fallback
                    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(dummy_frame, "FALLBACK MOCK CAMERA", (100, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
                    req_id = f"vision-req-{uuid.uuid4().hex[:8]}"
                    result = call_ai_vision(dummy_frame, motion_score, req_id)
                    publish_camera_event(result, motion_score, req_id)
        except Exception as e:
            print(f"[{SERVICE_NAME}] ❌ Fallback loop error: {e}")
            time.sleep(5)


# ── Camera Processing Loop ──
def camera_processing_loop():
    """Main loop: đọc frame thật từ CAMERA_URL, phát hiện motion, gọi AI Vision."""
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

    # Nhận diện nguồn camera (Nếu cấu hình là số nguyên 0, 1... thì dùng webcam)
    cam_source = CAMERA_URL
    try:
        if CAMERA_URL.isdigit():
            cam_source = int(CAMERA_URL)
    except Exception:
        pass

    print(f"[{SERVICE_NAME}] 📹 Connecting to camera source: {cam_source}")
    
    is_mjpeg_http = isinstance(cam_source, str) and (cam_source.startswith("http://") or cam_source.startswith("https://"))
    
    # Thử mở bằng VideoCapture trước
    cap = cv2.VideoCapture(cam_source)
    use_cv2_cap = cap.isOpened()

    if use_cv2_cap:
        CAMERA_STATUS["stream_connected"] = True
        print(f"[{SERVICE_NAME}] 📹 Camera stream connected via OpenCV VideoCapture!")
    elif is_mjpeg_http:
        print(f"[{SERVICE_NAME}] ⚠️ VideoCapture failed. Using custom HTTPS MJPEG reader...")
        CAMERA_STATUS["stream_connected"] = True
    else:
        CAMERA_STATUS["stream_connected"] = False
        print(f"[{SERVICE_NAME}] ❌ Failed to open camera. Fallback to mock loop.")
        fallback_camera_loop()
        return

    prev_frame = None

    if not use_cv2_cap and is_mjpeg_http:
        # Bộ đọc MJPEG stream bằng HTTPS thô
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            stream = urllib.request.urlopen(cam_source, context=ctx, timeout=15)
            bytes_buffer = b""
            print(f"[{SERVICE_NAME}] 📹 Custom HTTPS MJPEG Stream connected successfully!")
        except Exception as e:
            print(f"[{SERVICE_NAME}] ❌ Failed to connect custom MJPEG stream: {e}")
            CAMERA_STATUS["stream_connected"] = False
            fallback_camera_loop()
            return

        while True:
            try:
                chunk = stream.read(8192)
                if not chunk:
                    print(f"[{SERVICE_NAME}] ⚠️ Stream ended. Reconnecting...")
                    time.sleep(2)
                    stream = urllib.request.urlopen(cam_source, context=ctx, timeout=15)
                    bytes_buffer = b""
                    continue

                bytes_buffer += chunk
                a = bytes_buffer.find(b'\xff\xd8') # Start of JPEG marker
                b = bytes_buffer.find(b'\xff\xd9') # End of JPEG marker
                if a != -1 and b != -1:
                    jpg_bytes = bytes_buffer[a:b+2]
                    bytes_buffer = bytes_buffer[b+2:]
                    frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is None:
                        continue

                    CAMERA_STATUS["frames_captured"] += 1
                    frame_resized = cv2.resize(frame, (640, 480))

                    if prev_frame is None:
                        prev_frame = frame_resized.copy()
                        continue

                    motion_detected, motion_score = detect_motion(prev_frame, frame_resized)
                    prev_frame = frame_resized.copy()

                    if motion_detected:
                        now = time.time()
                        if now - last_trigger >= COOLDOWN_SECONDS:
                            last_trigger = now
                            CAMERA_STATUS["motion_triggers"] += 1
                            CAMERA_STATUS["last_motion"] = now_iso()
                            print(f"[{SERVICE_NAME}] 🏃 REAL Motion detected on URL stream! Score: {motion_score}")
                            req_id = f"vision-req-{uuid.uuid4().hex[:8]}"
                            result = call_ai_vision(frame_resized, motion_score, req_id)
                            publish_camera_event(result, motion_score, req_id)

                    time.sleep(0.05)
            except Exception as e:
                print(f"[{SERVICE_NAME}] ❌ HTTP stream read error: {e}")
                time.sleep(2)
                try:
                    stream = urllib.request.urlopen(cam_source, context=ctx, timeout=15)
                    bytes_buffer = b""
                except Exception:
                    pass
    else:
        # Đọc bằng VideoCapture
        while True:
            try:
                ret, frame = cap.read()
                if not ret:
                    print(f"[{SERVICE_NAME}] ⚠️ Failed to grab frame. Reconnecting...")
                    cap.release()
                    time.sleep(2)
                    cap = cv2.VideoCapture(cam_source)
                    continue

                CAMERA_STATUS["frames_captured"] += 1
                frame_resized = cv2.resize(frame, (640, 480))

                if prev_frame is None:
                    prev_frame = frame_resized.copy()
                    continue

                motion_detected, motion_score = detect_motion(prev_frame, frame_resized)
                prev_frame = frame_resized.copy()

                if motion_detected:
                    now = time.time()
                    if now - last_trigger >= COOLDOWN_SECONDS:
                        last_trigger = now
                        CAMERA_STATUS["motion_triggers"] += 1
                        CAMERA_STATUS["last_motion"] = now_iso()
                        print(f"[{SERVICE_NAME}] 🏃 REAL Motion detected! Score: {motion_score}")
                        req_id = f"vision-req-{uuid.uuid4().hex[:8]}"
                        result = call_ai_vision(frame_resized, motion_score, req_id)
                        publish_camera_event(result, motion_score, req_id)

                time.sleep(0.1)
            except Exception as e:
                print(f"[{SERVICE_NAME}] ❌ Camera loop error: {e}")
                time.sleep(5)

        cap.release()


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
