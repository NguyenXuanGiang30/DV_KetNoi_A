"""
A5: Analytics Service — Smart Campus
Subscribe 4 topic MQTT, tổng hợp metric và cung cấp REST API dashboard KPI.
"""

import json
import os
import ssl
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

SERVICE_NAME = os.getenv("SERVICE_NAME", "analytics")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "smart-campus-dev-token-2026")

# ── MQTT Config ──
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_IOT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_IOT_PASSWORD", "")

TOPIC_SENSOR = os.getenv("TOPIC_EVENTS_SENSOR", "smart-campus/events/sensor")
TOPIC_ACCESS = os.getenv("TOPIC_EVENTS_ACCESS", "smart-campus/events/access")
TOPIC_CAMERA = os.getenv("TOPIC_EVENTS_CAMERA", "smart-campus/events/camera")
TOPIC_CORE_ALERT = os.getenv("TOPIC_EVENTS_CORE_ALERT", "smart-campus/events/core-alert")

app = FastAPI(
    title="Smart Campus — Analytics Service",
    version=SERVICE_VERSION,
    description="Dịch vụ tổng hợp và phân tích dữ liệu từ tất cả các service.",
)

# ── Storage & Metrics ──
METRICS = {
    "sensor_events": 0,
    "access_events": 0,
    "camera_events": 0,
    "core_alerts": 0,
    "access_granted": 0,
    "access_denied": 0,
    "danger_count": 0,
    "warning_count": 0,
    "normal_count": 0,
    "sensor_error_count": 0,
    "low_battery_count": 0,
}
TEMP_BY_ROOM: Dict[str, List[float]] = defaultdict(list)
HUMIDITY_BY_ROOM: Dict[str, List[float]] = defaultdict(list)
RECENT_EVENTS: List[Dict] = []
MQTT_STATUS = {"connected": False, "message_count": 0}


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    time: str
    mqtt_connected: bool
    total_events: int


def verify_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization or authorization != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Event processors ──
def process_sensor_event(event: dict):
    METRICS["sensor_events"] += 1
    evt_status = event.get("status", "normal")
    METRICS[f"{evt_status}_count"] = METRICS.get(f"{evt_status}_count", 0) + 1

    location = event.get("location", "Unknown")
    temp = event.get("temperature_c")
    humidity = event.get("humidity_percent")
    if temp is not None:
        TEMP_BY_ROOM[location].append(temp)
        # Giữ tối đa 1000 giá trị gần nhất
        if len(TEMP_BY_ROOM[location]) > 1000:
            TEMP_BY_ROOM[location] = TEMP_BY_ROOM[location][-500:]
    if humidity is not None:
        HUMIDITY_BY_ROOM[location].append(humidity)
        if len(HUMIDITY_BY_ROOM[location]) > 1000:
            HUMIDITY_BY_ROOM[location] = HUMIDITY_BY_ROOM[location][-500:]

    battery = event.get("battery_percent", 100)
    if battery is not None and battery < 20:
        METRICS["low_battery_count"] += 1


def process_access_event(event: dict):
    METRICS["access_events"] += 1
    result = event.get("access_result", "")
    if result == "granted":
        METRICS["access_granted"] += 1
    elif result == "denied":
        METRICS["access_denied"] += 1


def process_camera_event(event: dict):
    METRICS["camera_events"] += 1


def process_core_alert(event: dict):
    METRICS["core_alerts"] += 1


# ── MQTT Client ──
def start_mqtt_client():
    try:
        from paho.mqtt import client as mqtt_client

        topics = [TOPIC_SENSOR, TOPIC_ACCESS, TOPIC_CAMERA, TOPIC_CORE_ALERT]

        def on_connect(client, userdata, flags, reason_code, properties=None):
            MQTT_STATUS["connected"] = True
            print(f"[{SERVICE_NAME}] ✅ Connected to HiveMQ")
            for topic in topics:
                client.subscribe(topic, qos=1)
                print(f"[{SERVICE_NAME}] 📡 Subscribed: {topic}")

        def on_disconnect(client, userdata, flags, reason_code, properties=None):
            MQTT_STATUS["connected"] = False

        def on_message(client, userdata, message):
            try:
                event = json.loads(message.payload.decode())
                MQTT_STATUS["message_count"] += 1
                RECENT_EVENTS.append({"topic": message.topic, "event": event, "at": now_iso()})
                if len(RECENT_EVENTS) > 500:
                    del RECENT_EVENTS[:250]

                if message.topic == TOPIC_SENSOR:
                    process_sensor_event(event)
                elif message.topic == TOPIC_ACCESS:
                    process_access_event(event)
                elif message.topic == TOPIC_CAMERA:
                    process_camera_event(event)
                elif message.topic == TOPIC_CORE_ALERT:
                    process_core_alert(event)

                total = sum([METRICS["sensor_events"], METRICS["access_events"],
                             METRICS["camera_events"], METRICS["core_alerts"]])
                if total % 10 == 0:
                    print(f"[{SERVICE_NAME}] 📊 Total events: {total} | "
                          f"Sensors: {METRICS['sensor_events']} | Access: {METRICS['access_events']} | "
                          f"Alerts: {METRICS['core_alerts']}")
            except Exception as e:
                print(f"[{SERVICE_NAME}] ❌ Error: {e}")

        client = mqtt_client.Client(protocol=mqtt_client.MQTTv5)
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message

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
    total = sum([METRICS["sensor_events"], METRICS["access_events"],
                 METRICS["camera_events"], METRICS["core_alerts"]])
    return HealthResponse(
        status="ok", service=SERVICE_NAME, version=SERVICE_VERSION,
        time=now_iso(), mqtt_connected=MQTT_STATUS["connected"],
        total_events=total,
    )


@app.get("/api/v1/metrics", dependencies=[Depends(verify_token)])
def get_all_metrics():
    """Dashboard KPI tổng hợp."""
    avg_temp = {}
    for room, temps in TEMP_BY_ROOM.items():
        if temps:
            avg_temp[room] = round(sum(temps) / len(temps), 1)

    avg_humidity = {}
    for room, hums in HUMIDITY_BY_ROOM.items():
        if hums:
            avg_humidity[room] = round(sum(hums) / len(hums), 1)

    total_access = METRICS["access_granted"] + METRICS["access_denied"]
    deny_rate = round(METRICS["access_denied"] / total_access * 100, 1) if total_access > 0 else 0

    return {
        "counters": METRICS,
        "avg_temperature_by_room": avg_temp,
        "avg_humidity_by_room": avg_humidity,
        "access_deny_rate_percent": deny_rate,
        "total_rooms_monitored": len(TEMP_BY_ROOM),
    }


@app.get("/api/v1/metrics/{metric_name}", dependencies=[Depends(verify_token)])
def get_metric(metric_name: str):
    if metric_name in METRICS:
        return {"metric": metric_name, "value": METRICS[metric_name]}
    if metric_name == "avg_temperature_by_room":
        return {room: round(sum(t) / len(t), 1) for room, t in TEMP_BY_ROOM.items() if t}
    if metric_name == "avg_humidity_by_room":
        return {room: round(sum(h) / len(h), 1) for room, h in HUMIDITY_BY_ROOM.items() if h}
    raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found")


@app.get("/api/v1/events/recent", dependencies=[Depends(verify_token)])
def get_recent_events(limit: int = 20):
    items = list(reversed(RECENT_EVENTS[-limit:]))
    return {"items": items}
