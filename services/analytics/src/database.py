import os
import sqlite3
import json
from datetime import datetime, timezone

DB_DIR = "/app/data"
DB_PATH = os.path.join(DB_DIR, "analytics.db")

def init_db():
    # Ensure database directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Table for received events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT UNIQUE,
        topic TEXT,
        event_type TEXT,
        source_service TEXT,
        timestamp TEXT,
        location TEXT,
        device_id TEXT,
        payload TEXT,
        received_at TEXT
    )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_topic ON events(topic)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
    
    # 2. Table for warning/danger alerts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        source TEXT,
        severity TEXT,
        location TEXT,
        message TEXT,
        timestamp TEXT,
        device_id TEXT,
        received_at TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    print(f"[Database] SQLite DB initialized at {DB_PATH}")

def save_event(topic: str, event: dict, received_at: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        event_id = event.get("event_id")
        event_type = event.get("event_type", "unknown")
        source_service = event.get("source_service", "unknown")
        timestamp = event.get("timestamp", received_at)
        location = event.get("location") or event.get("door_id") or "Unknown"
        device_id = event.get("device_id") or event.get("camera_id") or event.get("uid") or "unknown"
        payload_str = json.dumps(event)
        
        cursor.execute("""
        INSERT OR IGNORE INTO events 
        (event_id, topic, event_type, source_service, timestamp, location, device_id, payload, received_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, topic, event_type, source_service, timestamp, location, device_id, payload_str, received_at))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Database] Error saving event: {e}")
        return False

def save_alert(alert: dict, received_at: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT OR REPLACE INTO alerts 
        (id, source, severity, location, message, timestamp, device_id, received_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert["id"], 
            alert["source"], 
            alert["severity"], 
            alert["location"], 
            alert["message"], 
            alert["timestamp"], 
            alert["device_id"], 
            received_at
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Database] Error saving alert: {e}")
        return False

def load_metrics_counters() -> dict:
    """Rebuild METRICS counters from DB."""
    counters = {
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
        "invalid_device_count": 0
    }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Topic counts
        cursor.execute("SELECT topic, COUNT(*) FROM events GROUP BY topic")
        for topic, count in cursor.fetchall():
            if "sensor" in topic:
                counters["sensor_events"] = count
            elif "access" in topic:
                counters["access_events"] = count
            elif "camera" in topic:
                counters["camera_events"] = count
            elif "core-alert" in topic:
                counters["core_alerts"] = count
                
        # Access results
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN instr(payload, '"access_result": "granted"') > 0 THEN 1 ELSE 0 END),
                SUM(CASE WHEN instr(payload, '"access_result": "denied"') > 0 THEN 1 ELSE 0 END)
            FROM events WHERE topic LIKE '%access%'
        """)
        granted, denied = cursor.fetchone()
        counters["access_granted"] = granted or 0
        counters["access_denied"] = denied or 0
        
        # Status counts
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN instr(payload, '"status": "danger"') > 0 THEN 1 ELSE 0 END),
                SUM(CASE WHEN instr(payload, '"status": "warning"') > 0 THEN 1 ELSE 0 END),
                SUM(CASE WHEN instr(payload, '"status": "normal"') > 0 THEN 1 ELSE 0 END),
                SUM(CASE WHEN instr(payload, '"status": "sensor_error"') > 0 THEN 1 ELSE 0 END),
                SUM(CASE WHEN instr(payload, '"status": "invalid_device"') > 0 THEN 1 ELSE 0 END)
            FROM events WHERE topic LIKE '%sensor%'
        """)
        danger, warning, normal, err, invalid = cursor.fetchone()
        counters["danger_count"] = danger or 0
        counters["warning_count"] = warning or 0
        counters["normal_count"] = normal or 0
        counters["sensor_error_count"] = err or 0
        counters["invalid_device_count"] = invalid or 0
        
        # Low Battery counts (where battery_percent < 20)
        # Check matching string or load and parse payload
        cursor.execute("SELECT payload FROM events WHERE topic LIKE '%sensor%'")
        low_bat = 0
        for (payload_str,) in cursor.fetchall():
            try:
                evt = json.loads(payload_str)
                bat = evt.get("battery_percent")
                if bat is not None and bat < 20:
                    low_bat += 1
            except:
                pass
        counters["low_battery_count"] = low_bat
        
        conn.close()
    except Exception as e:
        print(f"[Database] Error loading metrics: {e}")
        
    return counters

def load_historical_events(limit=500) -> list:
    """Load recent events from DB."""
    events = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT topic, payload, received_at FROM events ORDER BY id DESC LIMIT ?", (limit,))
        for topic, payload_str, at in cursor.fetchall():
            try:
                event = json.loads(payload_str)
                # Clean sensitive info
                event.pop("uid", None)
                event.pop("full_name", None)
                event.pop("student_id", None)
                events.append({
                    "topic": topic,
                    "event": event,
                    "at": at
                })
            except:
                pass
        conn.close()
    except Exception as e:
        print(f"[Database] Error loading events: {e}")
    # Return chronologically ascending (as expected by RECENT_EVENTS backend logic)
    events.reverse()
    return events

def load_historical_alerts(limit=50) -> list:
    """Load alerts from DB."""
    alerts = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, source, severity, location, message, timestamp, device_id 
            FROM alerts ORDER BY received_at DESC, id DESC LIMIT ?
        """, (limit,))
        
        for r in cursor.fetchall():
            alerts.append({
                "id": r[0],
                "source": r[1],
                "severity": r[2],
                "location": r[3],
                "message": r[4],
                "timestamp": r[5],
                "device_id": r[6]
            })
        conn.close()
    except Exception as e:
        print(f"[Database] Error loading alerts: {e}")
    return alerts

def load_historical_climate() -> tuple:
    """Rebuild TEMP_BY_ROOM and HUMIDITY_BY_ROOM from DB."""
    temp_by_room = {}
    humidity_by_room = {}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT location, payload FROM events WHERE topic LIKE '%sensor%'")
        for loc, payload_str in cursor.fetchall():
            try:
                evt = json.loads(payload_str)
                t = evt.get("temperature_c")
                h = evt.get("humidity_percent")
                
                if t is not None:
                    if loc not in temp_by_room:
                        temp_by_room[loc] = []
                    temp_by_room[loc].append(t)
                    
                if h is not None:
                    if loc not in humidity_by_room:
                        humidity_by_room[loc] = []
                    humidity_by_room[loc].append(h)
            except:
                pass
        conn.close()
        
        # Cap length to last 500 for each room
        for loc in temp_by_room:
            if len(temp_by_room[loc]) > 1000:
                temp_by_room[loc] = temp_by_room[loc][-500:]
        for loc in humidity_by_room:
            if len(humidity_by_room[loc]) > 1000:
                humidity_by_room[loc] = humidity_by_room[loc][-500:]
                
    except Exception as e:
        print(f"[Database] Error loading climate data: {e}")
        
    return temp_by_room, humidity_by_room

def load_source_readiness() -> dict:
    """Get topic counts and last seen from DB."""
    topic_status = {
        "sensor": {"last_seen": None, "count": 0},
        "access": {"last_seen": None, "count": 0},
        "camera": {"last_seen": None, "count": 0},
        "core_alert": {"last_seen": None, "count": 0},
    }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT topic, COUNT(*), MAX(received_at) FROM events GROUP BY topic")
        for topic, count, last_seen in cursor.fetchall():
            if "sensor" in topic:
                topic_status["sensor"] = {"last_seen": last_seen, "count": count}
            elif "access" in topic:
                topic_status["access"] = {"last_seen": last_seen, "count": count}
            elif "camera" in topic:
                topic_status["camera"] = {"last_seen": last_seen, "count": count}
            elif "core-alert" in topic:
                topic_status["core_alert"] = {"last_seen": last_seen, "count": count}
                
        conn.close()
    except Exception as e:
        print(f"[Database] Error loading source readiness: {e}")
        
    return topic_status
