import os
import ssl
import time
from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv

load_dotenv()

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_IOT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_IOT_PASSWORD", "")

print(f"Connecting to: {MQTT_HOST}:{MQTT_PORT} as {MQTT_USERNAME}...")

connected = False

def on_connect(client, userdata, flags, reason_code, properties=None):
    global connected
    if reason_code == 0:
        print("[OK] Connected successfully!")
        connected = True
    else:
        print(f"[FAIL] Connection failed with code: {reason_code}")

def on_connect_fail(client, userdata, flags):
    print("[FAIL] Connection failed completely!")

client = mqtt_client.Client(protocol=mqtt_client.MQTTv5)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

try:
    # Method 1 from services
    client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
    
    # Method 2 from simulator (SSL Context)
    # context = ssl.create_default_context()
    # client.tls_set_context(context)
    
    client.on_connect = on_connect
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_start()
    
    time.sleep(3.0)
    client.loop_stop()
except Exception as e:
    print(f"Error during connect: {e}")
