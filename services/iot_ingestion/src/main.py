"""
A1: IoT Ingestion Service — Smart Campus
Subscribe dữ liệu cảm biến raw từ HiveMQ, validate, chuẩn hóa, phân loại trạng thái,
publish kết quả processed lên topic smart-campus/events/sensor.
"""

import csv
import json
import os
import ssl
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, status
from pydantic import BaseModel

SERVICE_NAME = os.getenv("SERVICE_NAME", "iot-ingestion")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")

# ── MQTT Config ──
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_IOT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_IOT_PASSWORD", "")
TOPIC_RAW = os.getenv("TOPIC_RAW_IOT", "smart-campus/raw/iot/environment")
TOPIC_EVENTS = os.getenv("TOPIC_EVENTS_SENSOR", "smart-campus/events/sensor")

app = FastAPI(
    title="Smart Campus — IoT Ingestion Service",
    version=SERVICE_VERSION,
    description="Dịch vụ tiếp nhận, chuẩn hóa và phân loại dữ liệu cảm biến môi trường.",
)

# ── In-memory storage ──
PROCESSED_EVENTS: List[Dict] = []
DEVICE_REGISTRY: Dict[str, Dict] = {}
MQTT_STATUS = {"connected": False, "last_message": None, "message_count": 0}


# ── Models ──
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    time: str
    mqtt_connected: bool
    message_count: int


# ── Load device registry ──
def load_device_registry():
    """Đọc danh sách thiết bị hợp lệ từ CSV."""
    global DEVICE_REGISTRY
    csv_paths = [
        Path(__file__).parent.parent.parent.parent / "Datas" / "IoT_device_registry.csv",
        Path("/app/data/IoT_device_registry.csv"),
        Path("Datas/IoT_device_registry.csv"),
    ]
    for csv_path in csv_paths:
        if csv_path.exists():
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    DEVICE_REGISTRY[row["device_id"].strip()] = {
                        "device_type": row.get("device_type", "").strip(),
                        "location": row.get("location", "").strip(),
                        "room": row.get("room", "").strip(),
                        "status": row.get("status", "").strip(),
                    }
            print(f"[{SERVICE_NAME}] ✅ Loaded {len(DEVICE_REGISTRY)} devices from {csv_path}")
            return
    print(f"[{SERVICE_NAME}] ⚠️ Device registry CSV not found, using empty registry")


# ── Helper for Safe Parsing ──
def safe_float(val, default=None):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

# ── Classification logic ──
def classify_environment(data: dict) -> tuple:
    """Phân loại trạng thái môi trường: (status, alert_level, reason)"""
    temp = safe_float(data.get("temperature_c"))
    humidity = safe_float(data.get("humidity_percent"))
    co2 = safe_float(data.get("co2_ppm"), 0.0)
    smoke = safe_float(data.get("smoke_ppm"), 0.0)
    battery = safe_float(data.get("battery_percent"), 100.0)
    device_id = data.get("device_id", "")

    # sensor_error: giá trị null hoặc không hợp lệ (safe_float trả về None)
    if temp is None or humidity is None:
        return "sensor_error", "medium", "missing_sensor_value"

    # invalid_device: thiết bị không có trong registry
    if device_id not in DEVICE_REGISTRY:
        return "invalid_device", "high", "device_not_registered"

    # danger
    if temp >= 40.0:
        return "danger", "high", "temperature_too_high"
    if co2 >= 1800.0:
        return "danger", "high", "co2_too_high"
    if smoke >= 1.0:
        return "danger", "high", "smoke_detected"

    # warning
    if temp >= 35.0:
        return "warning", "medium", "temperature_high"
    if humidity >= 85.0:
        return "warning", "medium", "humidity_high"
    if co2 >= 1200.0:
        return "warning", "medium", "co2_high"
    if smoke >= 0.5:
        return "warning", "medium", "smoke_warning"
    if battery < 20.0:
        return "warning", "low", "low_battery"

    return "normal", "none", "environment_normal"


def process_raw_event(raw_payload: dict) -> Optional[dict]:
    """Xử lý một event raw thành processed event."""
    # Validate required fields
    required = ["event_id", "event_type", "timestamp", "device_id", "temperature_c",
                 "humidity_percent", "motion_detected"]
    missing = [f for f in required if f not in raw_payload]
    if missing:
        print(f"[{SERVICE_NAME}] ❌ Missing fields: {missing}")
        return None

    # Cast raw values to appropriate types
    temp = safe_float(raw_payload.get("temperature_c"))
    humidity = safe_float(raw_payload.get("humidity_percent"))
    co2 = safe_float(raw_payload.get("co2_ppm"))
    smoke = safe_float(raw_payload.get("smoke_ppm"))
    battery = safe_float(raw_payload.get("battery_percent"))
    
    motion = raw_payload.get("motion_detected")
    if isinstance(motion, str):
        motion_detected = motion.lower() in ("true", "1", "yes")
    else:
        motion_detected = bool(motion)

    typed_payload = {
        "device_id": raw_payload.get("device_id"),
        "temperature_c": temp,
        "humidity_percent": humidity,
        "co2_ppm": co2,
        "smoke_ppm": smoke,
        "battery_percent": battery,
    }

    # Classify
    env_status, alert_level, reason = classify_environment(typed_payload)

    # Build processed event — loại bỏ scenario_hint_for_teacher
    event_id = f"sensor-event-{uuid.uuid4().hex[:8]}"
    processed = {
        "event_id": event_id,
        "event_type": "sensor.reading.processed",
        "source_service": SERVICE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "raw_event_id": raw_payload.get("event_id"),
        "device_id": raw_payload.get("device_id"),
        "location": raw_payload.get("location", "Unknown"),
        "temperature_c": temp,
        "humidity_percent": humidity,
        "motion_detected": motion_detected,
        "light_lux": safe_float(raw_payload.get("light_lux")),
        "co2_ppm": co2,
        "smoke_ppm": smoke,
        "battery_percent": battery,
        "status": env_status,
        "alert_level": alert_level,
        "reason": reason,
    }
    return processed


# ── MQTT Client ──
def start_mqtt_client():
    """Khởi động MQTT client trong background thread."""
    try:
        from paho.mqtt import client as mqtt_client

        def on_connect(client, userdata, flags, reason_code, properties=None):
            MQTT_STATUS["connected"] = True
            print(f"[{SERVICE_NAME}] ✅ Connected to HiveMQ: {reason_code}")
            client.subscribe(TOPIC_RAW, qos=1)
            print(f"[{SERVICE_NAME}] 📡 Subscribed to: {TOPIC_RAW}")

        def on_disconnect(client, userdata, flags, reason_code, properties=None):
            MQTT_STATUS["connected"] = False
            print(f"[{SERVICE_NAME}] ⚠️ Disconnected: {reason_code}")

        def on_message(client, userdata, message):
            try:
                raw = json.loads(message.payload.decode())
                MQTT_STATUS["last_message"] = datetime.now(timezone.utc).isoformat()
                MQTT_STATUS["message_count"] += 1

                processed = process_raw_event(raw)
                if processed:
                    PROCESSED_EVENTS.append(processed)
                    # Publish processed event
                    client.publish(TOPIC_EVENTS, json.dumps(processed), qos=1)
                    status_emoji = {"normal": "🟢", "warning": "🟡", "danger": "🔴",
                                    "sensor_error": "⚠️", "invalid_device": "❌"}.get(processed["status"], "❓")
                    print(f"[{SERVICE_NAME}] {status_emoji} [{processed['status']}] "
                          f"Device: {processed['device_id']} | Temp: {processed['temperature_c']}°C | "
                          f"Hum: {processed['humidity_percent']}% | CO2: {processed['co2_ppm']}ppm | "
                          f"Smoke: {processed['smoke_ppm']}ppm | Light: {processed['light_lux']}lux | "
                          f"Batt: {processed['battery_percent']}% | Motion: {processed['motion_detected']} | "
                          f"Reason: {processed['reason']}")
            except Exception as e:
                print(f"[{SERVICE_NAME}] ❌ Error processing message: {e}")

        client = mqtt_client.Client(protocol=mqtt_client.MQTTv5)
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message

        client.connect(MQTT_HOST, MQTT_PORT)
        client.loop_forever()
    except Exception as e:
        print(f"[{SERVICE_NAME}] ❌ MQTT connection failed: {e}")
        MQTT_STATUS["connected"] = False


# ── Startup ──
@app.on_event("startup")
async def startup():
    load_device_registry()
    thread = threading.Thread(target=start_mqtt_client, daemon=True)
    thread.start()
    print(f"[{SERVICE_NAME}] 🚀 Service started")


# ── Endpoints ──
@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        time=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        mqtt_connected=MQTT_STATUS["connected"],
        message_count=MQTT_STATUS["message_count"],
    )


@app.get("/api/v1/events/recent")
def get_recent_events(limit: int = 20):
    """Lấy danh sách event đã xử lý gần đây."""
    items = PROCESSED_EVENTS[-limit:]
    items_copy = list(reversed(items))
    return {"items": items_copy, "total": len(PROCESSED_EVENTS)}


@app.get("/api/v1/status")
def get_status():
    """Trạng thái chi tiết của service."""
    return {
        "service": SERVICE_NAME,
        "mqtt": MQTT_STATUS,
        "devices_registered": len(DEVICE_REGISTRY),
        "events_processed": len(PROCESSED_EVENTS),
    }
