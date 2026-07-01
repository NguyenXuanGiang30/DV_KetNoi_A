"""
A5: Analytics Service — Smart Campus
Subscribe 4 topic MQTT, tổng hợp metric và cung cấp REST API dashboard KPI.
"""

import json
import os
import random
import ssl
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import database

SERVICE_NAME = os.getenv("SERVICE_NAME", "analytics")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "smart-campus-dev-token-2026")

# ── MQTT Config ──
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "f6f78e87db4a4c189dd3d706745a5e93.s1.eu.hivemq.cloud")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_IOT_USERNAME", "DVKN_IOT_2026")
MQTT_PASSWORD = os.getenv("MQTT_IOT_PASSWORD", "ThaiBao12A@")

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

MQTT_TOPIC_STATUS = {
    "sensor": {"last_seen": None, "count": 0, "topic": TOPIC_SENSOR},
    "access": {"last_seen": None, "count": 0, "topic": TOPIC_ACCESS},
    "camera": {"last_seen": None, "count": 0, "topic": TOPIC_CAMERA},
    "core_alert": {"last_seen": None, "count": 0, "topic": TOPIC_CORE_ALERT},
}
ALERTS: List[Dict] = []
data_lock = threading.Lock()

DASHBOARD_HTML = ""
try:
    html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            DASHBOARD_HTML = f.read()
    else:
        print(f"dashboard.html not found at {html_path}")
except Exception as e:
    print(f"Failed to load dashboard.html: {e}")


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


# ── Threshold checks ──
def check_sensor_thresholds(event: dict) -> List[Dict]:
    alerts = []
    location = event.get("location", "Unknown")
    timestamp = event.get("timestamp", now_iso())
    device_id = event.get("device_id", "unknown-device")
    
    # Temp
    temp = event.get("temperature_c")
    if temp is not None:
        try:
            temp_val = float(temp)
            if temp_val >= 40:
                alerts.append({
                    "source": "sensor",
                    "severity": "danger",
                    "location": location,
                    "message": f"Nhiệt độ nguy hiểm tại {location}: {temp_val}°C (Ngưỡng: >= 40°C)",
                    "timestamp": timestamp,
                    "device_id": device_id
                })
            elif temp_val >= 35:
                alerts.append({
                    "source": "sensor",
                    "severity": "warning",
                    "location": location,
                    "message": f"Nhiệt độ cao tại {location}: {temp_val}°C (Ngưỡng: >= 35°C)",
                    "timestamp": timestamp,
                    "device_id": device_id
                })
        except ValueError:
            pass
            
    # Humidity
    hum = event.get("humidity_percent")
    if hum is not None:
        try:
            hum_val = float(hum)
            if hum_val >= 85:
                alerts.append({
                    "source": "sensor",
                    "severity": "warning",
                    "location": location,
                    "message": f"Độ ẩm quá cao tại {location}: {hum_val}% (Ngưỡng: >= 85%)",
                    "timestamp": timestamp,
                    "device_id": device_id
                })
        except ValueError:
            pass
        
    # CO2
    co2 = event.get("co2_ppm")
    if co2 is not None:
        try:
            co2_val = float(co2)
            if co2_val >= 1800:
                alerts.append({
                    "source": "sensor",
                    "severity": "danger",
                    "location": location,
                    "message": f"Nồng độ CO2 nguy hiểm tại {location}: {co2_val} ppm (Ngưỡng: >= 1800 ppm)",
                    "timestamp": timestamp,
                    "device_id": device_id
                })
            elif co2_val >= 1200:
                alerts.append({
                    "source": "sensor",
                    "severity": "warning",
                    "location": location,
                    "message": f"Nồng độ CO2 cao tại {location}: {co2_val} ppm (Ngưỡng: >= 1200 ppm)",
                    "timestamp": timestamp,
                    "device_id": device_id
                })
        except ValueError:
            pass
            
    # Smoke
    smoke = event.get("smoke_ppm")
    if smoke is not None:
        try:
            smoke_val = float(smoke)
            if smoke_val >= 1.0:
                alerts.append({
                    "source": "sensor",
                    "severity": "danger",
                    "location": location,
                    "message": f"Phát hiện khói nguy hiểm tại {location}: {smoke_val} ppm (Ngưỡng: >= 1.0 ppm)",
                    "timestamp": timestamp,
                    "device_id": device_id
                })
            elif smoke_val >= 0.5:
                alerts.append({
                    "source": "sensor",
                    "severity": "warning",
                    "location": location,
                    "message": f"Phát hiện khói cảnh báo tại {location}: {smoke_val} ppm (Ngưỡng: >= 0.5 ppm)",
                    "timestamp": timestamp,
                    "device_id": device_id
                })
        except ValueError:
            pass
            
    # Battery
    battery = event.get("battery_percent")
    if battery is not None:
        try:
            bat_val = float(battery)
            if bat_val < 20:
                alerts.append({
                    "source": "sensor",
                    "severity": "warning",
                    "location": location,
                    "message": f"Thiết bị {device_id} tại {location} yếu pin: {bat_val}% (Ngưỡng: < 20%)",
                    "timestamp": timestamp,
                    "device_id": device_id
                })
        except ValueError:
            pass
        
    # Check general status
    status = event.get("status")
    if status == "invalid_device":
        alerts.append({
            "source": "sensor",
            "severity": "danger",
            "location": location,
            "message": f"Thiết bị lạ/chưa đăng ký: {device_id} tại {location}",
            "timestamp": timestamp,
            "device_id": device_id
        })
    elif status == "sensor_error":
        alerts.append({
            "source": "sensor",
            "severity": "warning",
            "location": location,
            "message": f"Lỗi cảm biến: {event.get('reason', 'missing value')} tại {location}",
            "timestamp": timestamp,
            "device_id": device_id
        })
        
    return alerts


def check_camera_thresholds(event: dict) -> List[Dict]:
    alerts = []
    location = event.get("location", "Unknown")
    timestamp = event.get("timestamp", now_iso())
    camera_id = event.get("camera_id", "unknown-camera")
    
    # Motion score
    motion_score = event.get("motion_score")
    if motion_score is not None:
        try:
            score_val = float(motion_score)
            if score_val >= 0.8:
                alerts.append({
                    "source": "camera",
                    "severity": "warning",
                    "location": location,
                    "message": f"Phát hiện chuyển động lớn tại {location}: {round(score_val * 100)}% (Ngưỡng: >= 80%)",
                    "timestamp": timestamp,
                    "device_id": camera_id
                })
        except ValueError:
            pass
        
    # Unknown Person
    unknown_person = event.get("unknown_person")
    if unknown_person:
        alerts.append({
            "source": "camera",
            "severity": "danger",
            "location": location,
            "message": f"Cảnh báo người lạ xuất hiện tại {location}!",
            "timestamp": timestamp,
            "device_id": camera_id
        })
        
    # Risk Level
    risk_level = event.get("risk_level")
    if risk_level in ["warning", "danger"]:
        alerts.append({
            "source": "camera",
            "severity": risk_level,
            "location": location,
            "message": f"Cảnh báo rủi ro Camera: mức {risk_level.upper()} tại {location}",
            "timestamp": timestamp,
            "device_id": camera_id
        })
        
    return alerts


def generate_insights() -> List[str]:
    insights = []
    
    # 1. IoT Sensor Readiness & Stats
    total_rooms = len(TEMP_BY_ROOM)
    if total_rooms > 0:
        # Calculate overall avg temperature
        all_temps = []
        for temps in TEMP_BY_ROOM.values():
            all_temps.extend(temps)
        avg_temp = round(sum(all_temps) / len(all_temps), 1) if all_temps else 25.0
        
        # Check if any room has high average temp
        hot_rooms = []
        for room, temps in TEMP_BY_ROOM.items():
            if temps:
                room_avg = sum(temps) / len(temps)
                if room_avg >= 35:
                    hot_rooms.append(f"{room} ({round(room_avg, 1)}°C)")
        
        if hot_rooms:
            insights.append(f"🔥 Nhiệt độ trung bình cao bất thường tại: {', '.join(hot_rooms)}. Cần kiểm tra hệ thống làm mát.")
        else:
            insights.append(f"🌡️ Nhiệt độ trung bình toàn khu vực ổn định ở mức {avg_temp}°C (Giám sát {total_rooms} phòng).")
            
        # Humidity check
        all_hums = []
        for hums in HUMIDITY_BY_ROOM.values():
            all_hums.extend(hums)
        avg_hum = round(sum(all_hums) / len(all_hums), 1) if all_hums else 50.0
        if avg_hum >= 80:
            insights.append(f"💧 Độ ẩm trung bình cao ({avg_hum}%). Nguy cơ đọng nước và ảnh hưởng thiết bị.")
        else:
            insights.append(f"🍃 Độ ẩm không khí dễ chịu, trung bình {avg_hum}%.")
    else:
        insights.append("📡 Đang chờ dữ liệu cảm biến môi trường để phân tích khí hậu phòng.")
        
    # Low battery check
    low_bat = METRICS.get("low_battery_count", 0)
    if low_bat > 0:
        insights.append(f"🔋 Cảnh báo: Có {low_bat} thiết bị cảm biến ghi nhận mức pin dưới 20%. Cần bảo trì/thay pin.")
    else:
        insights.append("⚡ Năng lượng thiết bị: Tất cả cảm biến hoạt động tốt, không có thiết bị pin yếu.")
        
    # 2. Access Control Insights
    granted = METRICS.get("access_granted", 0)
    denied = METRICS.get("access_denied", 0)
    total_access = granted + denied
    if total_access > 0:
        deny_rate = round(denied / total_access * 100, 1)
        if deny_rate > 10:
            insights.append(f"⚠️ Tỉ lệ quẹt thẻ thất bại cao đột biến ({deny_rate}% trong {total_access} lượt). Kiểm tra lại whitelist.")
        else:
            insights.append(f"🚪 Kiểm soát ra vào ổn định. Đã xử lý {total_access} lượt quẹt thẻ (Từ chối: {deny_rate}%).")
    else:
        insights.append("🚪 Chưa ghi nhận lượt quẹt thẻ ra vào cửa.")
        
    # 3. Camera & AI motion
    cam_events = METRICS.get("camera_events", 0)
    if cam_events > 0:
        # Check if recent alerts contain unknown person
        unknown_alerts = [a for a in ALERTS if a["source"] == "camera" and "người lạ" in a["message"]]
        if unknown_alerts:
            insights.append(f"🚨 Cảnh báo an ninh: Phát hiện {len(unknown_alerts)} sự kiện xuất hiện người lạ từ Camera!")
        else:
            insights.append(f"📹 Hệ thống Camera hoạt động tốt, ghi nhận {cam_events} sự kiện chuyển động, không có người lạ.")
    else:
        insights.append("📹 Hệ thống Camera giám sát chưa gửi dữ liệu phân tích hình ảnh.")
        
    # 4. Readiness Summary
    online_count = sum(1 for status in MQTT_TOPIC_STATUS.values() if status["count"] > 0)
    if online_count == 4:
        insights.append("🟢 Tích hợp hoàn thành: Hệ thống đã kết nối đầy đủ dữ liệu từ cả 4 nguồn (A1, A2, A3, A6).")
    else:
        missing = [name for name, status in MQTT_TOPIC_STATUS.items() if status["count"] == 0]
        insights.append(f"🟡 Tích hợp chưa hoàn thành: Đang chờ dữ liệu từ {', '.join(missing)} ({online_count}/4 Online).")
        
    return insights


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
                now_str = now_iso()
                
                with data_lock:
                    MQTT_STATUS["message_count"] += 1
                    new_alerts = []
                    
                    if message.topic == TOPIC_SENSOR:
                        MQTT_TOPIC_STATUS["sensor"]["last_seen"] = now_str
                        MQTT_TOPIC_STATUS["sensor"]["count"] += 1
                        process_sensor_event(event)
                        new_alerts = check_sensor_thresholds(event)
                    elif message.topic == TOPIC_ACCESS:
                        MQTT_TOPIC_STATUS["access"]["last_seen"] = now_str
                        MQTT_TOPIC_STATUS["access"]["count"] += 1
                        process_access_event(event)
                    elif message.topic == TOPIC_CAMERA:
                        MQTT_TOPIC_STATUS["camera"]["last_seen"] = now_str
                        MQTT_TOPIC_STATUS["camera"]["count"] += 1
                        process_camera_event(event)
                        new_alerts = check_camera_thresholds(event)
                    elif message.topic == TOPIC_CORE_ALERT:
                        MQTT_TOPIC_STATUS["core_alert"]["last_seen"] = now_str
                        MQTT_TOPIC_STATUS["core_alert"]["count"] += 1
                        process_core_alert(event)
                        severity = event.get("severity", "medium").lower()
                        if severity not in ["low", "medium", "high", "critical"]:
                            severity = "medium"
                        if severity == "critical":
                            severity = "danger"
                        elif severity == "low":
                            severity = "warning"
                        elif severity == "high":
                            severity = "danger"
                        new_alerts = [{
                            "source": "core_alert",
                            "severity": severity,
                            "location": "System",
                            "message": f"Cảnh báo hệ thống ({event.get('alert_type', 'UNKNOWN')}): {event.get('message', '')}",
                            "timestamp": event.get("timestamp", now_str),
                            "device_id": "core-business"
                        }]
                        
                    for alert in new_alerts:
                        alert["id"] = f"alert-{int(datetime.now(timezone.utc).timestamp()*1000)}-{random.randint(1000, 9999)}"
                        ALERTS.insert(0, alert)
                        database.save_alert(alert, now_str)
                    if len(ALERTS) > 50:
                        del ALERTS[50:]
                        
                    database.save_event(message.topic, event, now_str)
                    
                    clean_event = dict(event)
                    clean_event.pop("uid", None)
                    clean_event.pop("full_name", None)
                    clean_event.pop("student_id", None)
                    
                    RECENT_EVENTS.append({"topic": message.topic, "event": clean_event, "at": now_str})
                    if len(RECENT_EVENTS) > 500:
                        del RECENT_EVENTS[:250]

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
    # Initialize DB & Restore State
    database.init_db()
    with data_lock:
        db_counters = database.load_metrics_counters()
        for k, v in db_counters.items():
            METRICS[k] = v
            
        db_temp, db_hum = database.load_historical_climate()
        for k, v in db_temp.items():
            TEMP_BY_ROOM[k] = v
        for k, v in db_hum.items():
            HUMIDITY_BY_ROOM[k] = v
            
        db_alerts = database.load_historical_alerts()
        ALERTS.extend(db_alerts)
        
        db_events = database.load_historical_events()
        RECENT_EVENTS.extend(db_events)
        
        db_readiness = database.load_source_readiness()
        for k, v in db_readiness.items():
            MQTT_TOPIC_STATUS[k]["last_seen"] = v["last_seen"]
            MQTT_TOPIC_STATUS[k]["count"] = v["count"]
            
    threading.Thread(target=start_mqtt_client, daemon=True).start()
    print(f"[{SERVICE_NAME}] 🚀 Service started and state restored from database")


# ── REST Endpoints ──

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    try:
        html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    except Exception as e:
        print(f"Error reloading dashboard.html: {e}")
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/health", response_model=HealthResponse)
def health():
    with data_lock:
        total = sum([METRICS["sensor_events"], METRICS["access_events"],
                     METRICS["camera_events"], METRICS["core_alerts"]])
        return HealthResponse(
            status="ok", service=SERVICE_NAME, version=SERVICE_VERSION,
            time=now_iso(), mqtt_connected=MQTT_STATUS["connected"],
            total_events=total,
        )


@app.get("/api/v1/dashboard/data")
def get_dashboard_data():
    with data_lock:
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

        insights = generate_insights()
        recent_alerts = list(ALERTS)
        
        short_events = []
        for item in RECENT_EVENTS[-20:]:
            topic = item["topic"]
            evt = item["event"]
            at = item["at"]
            
            if topic == TOPIC_SENSOR:
                msg = f"Cảm biến {evt.get('device_id')} tại {evt.get('location')} báo {evt.get('status')} (Temp: {evt.get('temperature_c')}°C)"
            elif topic == TOPIC_ACCESS:
                msg = f"Quẹt thẻ tại cửa {evt.get('door_id')} -> {evt.get('access_result', 'unknown').upper()}"
            elif topic == TOPIC_CAMERA:
                msg = f"Camera {evt.get('camera_id')} phát hiện chuyển động ({round(evt.get('motion_score', 0)*100)}%)"
            elif topic == TOPIC_CORE_ALERT:
                msg = f"Cảnh báo hệ thống {evt.get('alert_type')}: {evt.get('message')}"
            else:
                msg = f"Sự kiện mới trên kênh {topic}"
                
            short_events.append({
                "topic": topic,
                "message": msg,
                "at": at
            })
            
        short_events.reverse()

        return {
            "metrics": METRICS,
            "avg_temperature_by_room": avg_temp,
            "avg_humidity_by_room": avg_humidity,
            "access_deny_rate_percent": deny_rate,
            "mqtt_status": MQTT_STATUS,
            "topic_status": MQTT_TOPIC_STATUS,
            "insights": insights,
            "alerts": recent_alerts,
            "recent_events": short_events
        }


@app.post("/api/v1/services/check/{service_key}")
def check_partner_service(service_key: str):
    # Map service key to container health endpoints in the Docker network
    url_map = {
        "sensor": "http://iot-ingestion:8000/health",
        "access": "http://access-gate:8000/health",
        "camera": "http://camera-stream:8000/health",
        "core_alert": "http://core-business:8000/health"
    }
    
    if service_key not in url_map:
        raise HTTPException(status_code=400, detail="Invalid service key")
        
    url = url_map[service_key]
    
    import urllib.request
    import urllib.error
    
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as response:
            status = response.getcode()
            if status == 200:
                with data_lock:
                    now_str = now_iso()
                    MQTT_TOPIC_STATUS[service_key]["last_seen"] = now_str
                    if MQTT_TOPIC_STATUS[service_key]["count"] == 0:
                        MQTT_TOPIC_STATUS[service_key]["count"] = 1 # Mark as active
                return {"online": True, "details": "Kết nối thành công (HTTP 200)"}
    except urllib.error.URLError as e:
        print(f"Connection check failed for {service_key}: {e}")
    except Exception as e:
        print(f"Exception during check for {service_key}: {e}")
        
    return {"online": False, "details": "Không thể kết nối tới dịch vụ đối tác"}


@app.get("/api/v1/metrics", dependencies=[Depends(verify_token)])
def get_all_metrics():
    """Dashboard KPI tổng hợp."""
    with data_lock:
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
    with data_lock:
        if metric_name in METRICS:
            return {"metric": metric_name, "value": METRICS[metric_name]}
        if metric_name == "avg_temperature_by_room":
            return {room: round(sum(t) / len(t), 1) for room, t in TEMP_BY_ROOM.items() if t}
        if metric_name == "avg_humidity_by_room":
            return {room: round(sum(h) / len(h), 1) for room, h in HUMIDITY_BY_ROOM.items() if h}
        raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found")


@app.get("/api/v1/events/recent", dependencies=[Depends(verify_token)])
def get_recent_events(limit: int = 20):
    with data_lock:
        items = list(reversed(RECENT_EVENTS[-limit:]))
        return {"items": items}
