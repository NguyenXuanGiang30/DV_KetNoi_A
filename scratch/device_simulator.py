import os
import ssl
import time
import json
import csv
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Config ---
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USER = os.getenv("MQTT_GATE_USERNAME", "")
MQTT_PASS = os.getenv("MQTT_GATE_PASSWORD", "")

TOPIC_RAW_IOT = os.getenv("TOPIC_RAW_IOT", "smart-campus/raw/iot/environment")
TOPIC_RAW_ACCESS = os.getenv("TOPIC_RAW_ACCESS", "smart-campus/raw/access/rfid-uid")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
WHITELIST_PATH = BASE_DIR / "Datas" / "Acessgate_uid_whitelist.csv"
REGISTRY_PATH = BASE_DIR / "Datas" / "IoT_device_registry.csv"

# --- Load Data ---
def load_uids():
    uids = []
    if WHITELIST_PATH.exists():
        with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uids.append(row["uid"].strip())
    else:
        # Fallback UIDs if CSV not found
        uids = [f"04:A1:B2:C3:D4:0{i}" for i in range(1, 6)]
    return uids

def load_devices():
    devices = []
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                devices.append({
                    "id": row["device_id"].strip(),
                    "location": row["location"].strip()
                })
    else:
        devices = [{"id": "esp32-library-01", "location": "Library 01"}]
    return devices

# Start values for sensors
def init_sensor_states(devices):
    states = {}
    for dev in devices:
        states[dev["id"]] = {
            "temp": round(random.uniform(24.0, 27.0), 1),
            "humidity": round(random.uniform(50.0, 60.0), 1),
            "light": round(random.uniform(300.0, 500.0), 1),
            "co2": round(random.uniform(400.0, 600.0), 1),
            "smoke": round(random.uniform(0.01, 0.05), 2),
            "battery": 100
        }
    return states

def update_sensor_states(states):
    for dev_id, s in states.items():
        # Random walk variations
        s["temp"] = round(s["temp"] + random.uniform(-0.3, 0.3), 1)
        s["temp"] = max(18.0, min(42.0, s["temp"]))  # clamp
        
        s["humidity"] = round(s["humidity"] + random.uniform(-0.5, 0.5), 1)
        s["humidity"] = max(30.0, min(95.0, s["humidity"]))
        
        s["light"] = round(s["light"] + random.uniform(-10.0, 10.0), 1)
        s["light"] = max(0.0, min(1000.0, s["light"]))
        
        s["co2"] = round(s["co2"] + random.uniform(-15.0, 15.0), 1)
        s["co2"] = max(350.0, min(2000.0, s["co2"]))
        
        s["smoke"] = round(s["smoke"] + random.uniform(-0.01, 0.01), 2)
        s["smoke"] = max(0.0, min(2.5, s["smoke"]))
        
        # Slowly drain battery or stay high
        if random.random() < 0.05:
            s["battery"] = max(5, s["battery"] - 1)
            
        # Simulate occasional high anomaly in one specific room
        if dev_id == "esp32-lab-a102" and random.random() < 0.01:
            print("[WARNING] [Simulator] Triggering a high temperature fire anomaly in Lab A102 for testing core business alerts!")
            s["temp"] = 38.5
            s["smoke"] = 1.2
            s["co2"] = 1350.0

# Connect to MQTT
def connect_mqtt():
    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print("[OK] [Simulator] Connected successfully to HiveMQ Cloud Broker!")
        else:
            print(f"[ERROR] [Simulator] Connection failed with code {reason_code}")

    client = mqtt_client.Client(protocol=mqtt_client.MQTTv5)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    
    # Use SSL/TLS
    context = ssl.create_default_context()
    client.tls_set_context(context)
    
    client.on_connect = on_connect
    
    print(f"[CONNECT] [Simulator] Connecting to broker {MQTT_HOST}:{MQTT_PORT}...")
    client.connect(MQTT_HOST, MQTT_PORT)
    return client

def main():
    print("[INFO] Starting Smart Campus Device & Card Swipe Simulator...")
    uids = load_uids()
    devices = load_devices()
    sensor_states = init_sensor_states(devices)
    
    print(f"Loaded {len(uids)} whitelisted UIDs.")
    print(f"Loaded {len(devices)} environment devices.")
    
    client = connect_mqtt()
    client.loop_start()
    
    last_sensor_pub = 0.0
    last_access_pub = 0.0
    
    # Loop intervals
    SENSOR_INTERVAL = 5.0  # seconds
    ACCESS_INTERVAL = 15.0 # seconds
    
    try:
        while True:
            now = time.time()
            iso_now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            
            # 1. Publish Sensor Telemetry
            if now - last_sensor_pub >= SENSOR_INTERVAL:
                update_sensor_states(sensor_states)
                
                # Pick a random device to publish
                dev = random.choice(devices)
                dev_id = dev["id"]
                s = sensor_states[dev_id]
                
                payload = {
                    "event_id": f"sim-sensor-{uuid.uuid4().hex[:8]}",
                    "event_type": "sensor.raw",
                    "timestamp": iso_now,
                    "device_id": dev_id,
                    "location": dev["location"],
                    "temperature_c": s["temp"],
                    "humidity_percent": s["humidity"],
                    "motion_detected": random.choice([True, False, False, False]),  # 25% motion
                    "light_lux": s["light"],
                    "co2_ppm": s["co2"],
                    "smoke_ppm": s["smoke"],
                    "battery_percent": s["battery"]
                }
                
                client.publish(TOPIC_RAW_IOT, json.dumps(payload), qos=1)
                print(f"[SENSOR] [Simulator] Published SENSOR: {dev_id} | Temp: {s['temp']}C | CO2: {s['co2']}ppm | Smoke: {s['smoke']}")
                last_sensor_pub = now
                
            # 2. Publish Card Swipe
            if now - last_access_pub >= ACCESS_INTERVAL:
                # 85% chance of valid card swipe, 15% chance of invalid/unregistered card swipe
                if random.random() < 0.85:
                    uid = random.choice(uids)
                    valid_str = "WHITELISTED"
                else:
                    uid = f"99:AA:BB:CC:{random.randint(10,99)}:{random.randint(10,99)}"
                    valid_str = "UNREGISTERED"
                
                door = random.choice(["gate-a", "gate-b"])
                location = "Main Gate A" if door == "gate-a" else "Main Gate B"
                direction = random.choice(["in", "out"])
                
                payload = {
                    "event_id": f"sim-access-{uuid.uuid4().hex[:8]}",
                    "event_type": "access.raw",
                    "timestamp": iso_now,
                    "uid": uid,
                    "door_id": door,
                    "direction": direction,
                    "location": location
                }
                
                client.publish(TOPIC_RAW_ACCESS, json.dumps(payload), qos=1)
                print(f"[CARD] [Simulator] Published CARD SWIPE: {uid} ({valid_str}) at {location} going {direction.upper()}")
                last_access_pub = now
                
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n[INFO] Stopping simulator...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[OK] Simulator stopped.")

if __name__ == "__main__":
    main()
