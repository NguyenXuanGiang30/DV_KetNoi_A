"""
A3: Access Gate Service — Smart Campus
Subscribe UID RFID raw từ HiveMQ, đối chiếu whitelist, gọi Core Business kiểm tra policy,
publish kết quả processed, và cung cấp REST API cho Core truy vấn log.
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

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

SERVICE_NAME = os.getenv("SERVICE_NAME", "access-gate")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "smart-campus-dev-token-2026")

# ── MQTT Config ──
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_GATE_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_GATE_PASSWORD", "")
TOPIC_RAW = os.getenv("TOPIC_RAW_ACCESS", "smart-campus/raw/access/rfid-uid")
TOPIC_EVENTS = os.getenv("TOPIC_EVENTS_ACCESS", "smart-campus/events/access")

# ── Core Business URL (cặp 10) ──
CORE_BUSINESS_URL = os.getenv("CORE_BUSINESS_URL", "http://core-business:8006")

app = FastAPI(
    title="Smart Campus — Access Gate Service",
    version=SERVICE_VERSION,
    description="Dịch vụ kiểm soát ra/vào: nhận UID RFID, đối chiếu whitelist, publish kết quả.",
)

# ── In-memory storage ──
ACCESS_LOGS: List[Dict] = []
UID_WHITELIST: Dict[str, Dict] = {}
GATE_STATUS: Dict[str, Dict] = {
    "gate-a": {"gate_id": "gate-a", "location": "Main Gate A", "status": "operational"},
    "gate-b": {"gate_id": "gate-b", "location": "Main Gate B", "status": "operational"},
}
MQTT_STATUS = {"connected": False, "last_message": None, "message_count": 0}


# ── Models ──
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    time: str
    mqtt_connected: bool
    message_count: int


class AccessLogItem(BaseModel):
    log_id: str
    event_id: str
    uid: str
    student_id: Optional[str]
    full_name: Optional[str]
    class_name: Optional[str]
    door_id: str
    location: str
    direction: str
    access_result: str
    reason: str
    timestamp: str


class GateStatus(BaseModel):
    gate_id: str
    location: str
    status: str


class CardInfo(BaseModel):
    uid: str
    student_id: Optional[str]
    full_name: Optional[str]
    class_name: Optional[str]
    registered: bool


# ── Auth ──
def verify_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if authorization != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid bearer token")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Load UID whitelist ──
def load_uid_whitelist():
    """Đọc danh sách UID hợp lệ từ CSV."""
    global UID_WHITELIST
    csv_paths = [
        Path(__file__).parent.parent.parent.parent / "Datas" / "Acessgate_uid_whitelist.csv",
        Path("/app/data/Acessgate_uid_whitelist.csv"),
        Path("Datas/Acessgate_uid_whitelist.csv"),
    ]
    for csv_path in csv_paths:
        if csv_path.exists():
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    uid = row["uid"].strip()
                    UID_WHITELIST[uid] = {
                        "student_id": row.get("student_id", "").strip(),
                        "full_name": row.get("full_name", "").strip(),
                        "class_name": row.get("class_name", "").strip(),
                    }
            print(f"[{SERVICE_NAME}] ✅ Loaded {len(UID_WHITELIST)} UIDs from {csv_path}")
            return
    print(f"[{SERVICE_NAME}] ⚠️ UID whitelist CSV not found, using empty whitelist")


# ── Process RFID event ──
def process_rfid_event(raw: dict) -> Optional[dict]:
    """Xử lý event quẹt thẻ RFID raw."""
    required = ["event_id", "event_type", "timestamp", "uid", "door_id", "direction"]
    missing = [f for f in required if f not in raw]
    if missing:
        print(f"[{SERVICE_NAME}] ❌ Missing fields: {missing}")
        return None

    uid = raw["uid"]
    student = UID_WHITELIST.get(uid)

    if student:
        access_result = "granted"
        reason = "uid_matched"
        student_id = student["student_id"]
        full_name = student["full_name"]
        class_name = student["class_name"]
    else:
        access_result = "denied"
        reason = "uid_not_found"
        student_id = None
        full_name = None
        class_name = None

    event_id = f"access-event-{uuid.uuid4().hex[:8]}"
    processed = {
        "event_id": event_id,
        "event_type": "access.swipe.processed",
        "source_service": SERVICE_NAME,
        "timestamp": now_iso(),
        "raw_event_id": raw.get("event_id"),
        "uid": uid,
        "student_id": student_id,
        "full_name": full_name,
        "class_name": class_name,
        "door_id": raw.get("door_id", "unknown"),
        "location": raw.get("location", "Unknown"),
        "direction": raw.get("direction", "unknown"),
        "access_result": access_result,
        "reason": reason,
    }
    return processed


# ── Optional: Check policy with Core Business (cặp 10) ──
async def check_policy_with_core(uid: str, door_id: str, direction: str) -> Optional[dict]:
    """Gọi Core Business kiểm tra policy ra/vào (có thể thất bại — fail-open)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{CORE_BUSINESS_URL}/access/check",
                json={"uid": uid, "door_id": door_id, "direction": direction},
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"[{SERVICE_NAME}] ⚠️ Core Business policy check failed: {e}")
    return None  # fail-open: nếu Core không trả lời, vẫn dùng kết quả whitelist


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
                MQTT_STATUS["last_message"] = now_iso()
                MQTT_STATUS["message_count"] += 1

                processed = process_rfid_event(raw)
                if processed:
                    ACCESS_LOGS.append(processed)
                    client.publish(TOPIC_EVENTS, json.dumps(processed), qos=1)
                    emoji = "✅" if processed["access_result"] == "granted" else "🚫"
                    name = processed["full_name"] or "Unknown"
                    print(f"[{SERVICE_NAME}] {emoji} [{processed['access_result'].upper()}] "
                          f"UID: {processed['uid']} | Name: {name} | Gate: {processed['door_id']}")
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
        print(f"[{SERVICE_NAME}] ❌ MQTT connection failed: {e}")
        MQTT_STATUS["connected"] = False


# ── Startup ──
@app.on_event("startup")
async def startup():
    load_uid_whitelist()
    thread = threading.Thread(target=start_mqtt_client, daemon=True)
    thread.start()
    print(f"[{SERVICE_NAME}] 🚀 Service started")


# ── REST Endpoints ──

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok", service=SERVICE_NAME, version=SERVICE_VERSION,
        time=now_iso(), mqtt_connected=MQTT_STATUS["connected"],
        message_count=MQTT_STATUS["message_count"],
    )


@app.get("/access/logs/recent", dependencies=[Depends(verify_token)])
def get_recent_logs(limit: int = Query(default=20, ge=1, le=100)):
    """Cặp 3: Core Business gọi — lấy log quẹt thẻ gần đây."""
    items = list(reversed(ACCESS_LOGS[-limit:]))
    return {"items": items, "total": len(ACCESS_LOGS)}


@app.get("/access/logs/{log_id}", dependencies=[Depends(verify_token)])
def get_log_by_id(log_id: str):
    """Cặp 3: Lấy chi tiết một log."""
    for log in ACCESS_LOGS:
        if log["event_id"] == log_id:
            return log
    raise HTTPException(status_code=404, detail=f"Log {log_id} not found")


@app.get("/gates/{gate_id}/status", response_model=GateStatus, dependencies=[Depends(verify_token)])
def get_gate_status(gate_id: str):
    """Cặp 3: Lấy trạng thái cổng."""
    gate = GATE_STATUS.get(gate_id)
    if not gate:
        raise HTTPException(status_code=404, detail=f"Gate {gate_id} not found")
    return GateStatus(**gate)


@app.get("/cards/{card_uid}", response_model=CardInfo, dependencies=[Depends(verify_token)])
def get_card_info(card_uid: str):
    """Cặp 3: Tra cứu thông tin thẻ RFID."""
    student = UID_WHITELIST.get(card_uid)
    if student:
        return CardInfo(uid=card_uid, registered=True, **student)
    return CardInfo(uid=card_uid, student_id=None, full_name=None, class_name=None, registered=False)
