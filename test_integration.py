import httpx
import json
import time
import ssl
import sys
from paho.mqtt import client as mqtt_client

# --- Configuration ---
AUTH_TOKEN = "smart-campus-dev-token-2026"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

SERVICES = {
    "A1: IoT Ingestion": "http://localhost:8001",
    "A2: Camera Stream": "http://localhost:8002",
    "A3: Access Gate": "http://localhost:8003",
    "A4: AI Vision": "http://localhost:8004",
    "A5: Analytics": "http://localhost:8005",
    "A6: Core Business": "http://localhost:8006",
    "A7: Notification": "http://localhost:8007",
}

MQTT_HOST = "f6f78e87db4a4c189dd3d706745a5e93.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "DVKN2026"
MQTT_PASS = "ThaiBao12A@"

TOPIC_RAW_IOT = "smart-campus/raw/iot/environment"
TOPIC_RAW_ACCESS = "smart-campus/raw/access/rfid-uid"

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def test_healthchecks():
    print_header("1. HEALTHCHECK VERIFICATION")
    all_ok = True
    for name, url in SERVICES.items():
        try:
            resp = httpx.get(f"{url}/health", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                mqtt_connected = data.get("mqtt_connected", False)
                print(f"[+] {name:<20} : OK (HTTP 200) | MQTT: {mqtt_connected}")
            else:
                print(f"[-] {name:<20} : FAILED (HTTP {resp.status_code})")
                all_ok = False
        except Exception as e:
            print(f"[X] {name:<20} : UNREACHABLE ({e})")
            all_ok = False
    return all_ok

def test_rest_apis():
    print_header("2. REST API INTEGRATION VERIFICATION")
    
    # 2.1. AI Vision - POST /detect (Camera Stream calls this)
    try:
        payload = {
            "camera_id": "cam-gate-a",
            "image_url": "https://example.com/frame.jpg",
            "timestamp": "2026-06-15T07:00:00Z",
            "motion_score": 0.85
        }
        resp = httpx.post(f"{SERVICES['A4: AI Vision']}/detect", json=payload, headers=HEADERS, timeout=3.0)
        print(f"[+] AI Vision POST /detect : Status {resp.status_code} | Result: {resp.json().get('detection_id')}")
    except Exception as e:
        print(f"[X] AI Vision POST /detect FAILED: {e}")

    # 2.2. AI Vision - POST /vision/face-match (Core Business calls this)
    try:
        payload = {
            "camera_id": "cam-gate-a",
            "image_url": "https://example.com/frame.jpg",
            "reference_face_id": "ref-123"
        }
        resp = httpx.post(f"{SERVICES['A4: AI Vision']}/vision/face-match", json=payload, headers=HEADERS, timeout=3.0)
        print(f"[+] AI Vision POST /face-match : Status {resp.status_code} | Match: {resp.json().get('matched', False)}")
    except Exception as e:
        print(f"[X] AI Vision POST /face-match FAILED: {e}")

    # 2.3. Core Business - POST /access/check (Access Gate calls this)
    try:
        payload = {"uid": "04:A1:B2:C3:D4:05", "door_id": "gate-a", "direction": "in"}
        resp = httpx.post(f"{SERVICES['A6: Core Business']}/access/check", json=payload, headers=HEADERS, timeout=3.0)
        print(f"[+] Core Business POST /access/check : Status {resp.status_code} | Decision: {resp.json().get('decision', 'denied')}")
    except Exception as e:
        print(f"[X] Core Business POST /access/check FAILED: {e}")

    # 2.4. Access Gate - GET /access/logs/recent (Core Business calls this)
    try:
        resp = httpx.get(f"{SERVICES['A3: Access Gate']}/access/logs/recent?limit=3", headers=HEADERS, timeout=3.0)
        print(f"[+] Access Gate GET /access/logs/recent : Status {resp.status_code} | Total logs: {resp.json().get('total', 0)}")
    except Exception as e:
        print(f"[X] Access Gate GET /access/logs/recent FAILED: {e}")

    # 2.5. Notification - POST /api/v1/notifications (Core Business calls this)
    try:
        payload = {
            "source_service": "core-business",
            "alert_type": "FIRE_WARNING",
            "severity": "HIGH",
            "message": "WARNING: High temperature detected in Lab A102!",
            "channels": ["console", "telegram"]
        }
        resp = httpx.post(f"{SERVICES['A7: Notification']}/api/v1/notifications", json=payload, headers=HEADERS, timeout=3.0)
        print(f"[+] Notification POST /api/v1/notifications : Status {resp.status_code} | Resp: {resp.json().get('status')}")
    except Exception as e:
        print(f"[X] Notification POST /api/v1/notifications FAILED: {e}")

def publish_mqtt_message(topic, payload):
    """Publish an MQTT message via HiveMQ TLS."""
    try:
        client = mqtt_client.Client(protocol=mqtt_client.MQTTv5)
        client.username_pw_set(MQTT_USER, MQTT_PASS)
        client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        
        # Connect with timeout
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=10)
        
        # Publish
        info = client.publish(topic, json.dumps(payload), qos=1)
        info.wait_for_publish(timeout=5.0)
        client.disconnect()
        return True
    except Exception as e:
        print(f"[X] MQTT Publish FAILED: {e}")
        return False

def test_mqtt_flows():
    print_header("3. ASYNCHRONOUS MQTT E2E FLOWS")
    
    # 3.1. Test raw sensor event
    sensor_payload = {
        "event_id": f"test-raw-sensor-{int(time.time())}",
        "event_type": "sensor.raw",
        "timestamp": "2026-06-15T07:00:00Z",
        "device_id": "esp32-library-01",
        "temperature_c": 27.5,
        "humidity_percent": 55.4,
        "motion_detected": False,
        "light_lux": 400,
        "co2_ppm": 500,
        "smoke_ppm": 0.05,
        "battery_percent": 98
    }
    
    print("[*] Publishing RAW SENSOR event to HiveMQ Cloud...")
    if publish_mqtt_message(TOPIC_RAW_IOT, sensor_payload):
        print("[+] Published SENSOR successfully. Waiting 3s for processing...")
        time.sleep(3.0)
        
        try:
            resp = httpx.get(f"{SERVICES['A1: IoT Ingestion']}/api/v1/events/recent?limit=3")
            events = resp.json().get("items", [])
            matched = False
            for ev in events:
                if ev.get("raw_event_id") == sensor_payload["event_id"]:
                    print(f"[+] IoT Ingestion RECEIVED AND PROCESSED successfully!")
                    print(f"    - Processed Event ID: {ev.get('event_id')}")
                    print(f"    - Status: {ev.get('status')} | Reason: {ev.get('reason')}")
                    matched = True
                    break
            if not matched:
                print("[-] Event not found in IoT Ingestion recent events list.")
        except Exception as e:
            print(f"[X] Failed to query IoT Ingestion recent events: {e}")

    # 3.2. Test raw RFID event
    rfid_payload = {
        "event_id": f"test-raw-rfid-{int(time.time())}",
        "event_type": "access.raw",
        "timestamp": "2026-06-15T07:00:00Z",
        "uid": "04:A1:B2:C3:D4:05",  # In whitelist
        "door_id": "gate-a",
        "direction": "in",
        "location": "Main Gate A"
    }
    
    print("\n[*] Publishing RAW RFID swipe event to HiveMQ Cloud...")
    if publish_mqtt_message(TOPIC_RAW_ACCESS, rfid_payload):
        print("[+] Published RFID successfully. Waiting 3s for processing...")
        time.sleep(3.0)
        
        try:
            resp = httpx.get(f"{SERVICES['A3: Access Gate']}/access/logs/recent?limit=3", headers=HEADERS)
            logs = resp.json().get("items", [])
            matched = False
            for log in logs:
                if log.get("raw_event_id") == rfid_payload["event_id"]:
                    print(f"[+] Access Gate RECEIVED AND PROCESSED successfully!")
                    print(f"    - Student Name: {log.get('full_name')} | Result: {log.get('access_result').upper()}")
                    matched = True
                    break
            if not matched:
                print("[-] Swipe log not found in Access Gate log list.")
        except Exception as e:
            print(f"[X] Failed to query Access Gate logs: {e}")

def test_analytics_metrics():
    print_header("4. ANALYTICS METRICS VERIFICATION (A5)")
    try:
        resp = httpx.get(f"{SERVICES['A5: Analytics']}/api/v1/metrics", headers=HEADERS)
        data = resp.json()
        print(f"[+] Analytics Summary:")
        counters = data.get("counters", {})
        print(f"    - Total Sensor Events: {counters.get('sensor_events', 0)}")
        print(f"    - Total Access Events: {counters.get('access_events', 0)}")
        print(f"    - Total Alerts: {counters.get('core_alerts', 0)}")
        print(f"    - Total Rooms Monitored: {data.get('total_rooms_monitored', 0)}")
    except Exception as e:
        print(f"[X] Analytics Query FAILED: {e}")

if __name__ == "__main__":
    print("STARTING E2E INTEGRATION TESTING SCRIPT\n")
    health_ok = test_healthchecks()
    if not health_ok:
        print("\n[!] Warning: Some services are not responding. Ensure Docker is running.")
    
    test_rest_apis()
    test_mqtt_flows()
    test_analytics_metrics()
    
    print_header("TEST RUN COMPLETED")
