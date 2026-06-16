# Event Contract: Sensor Event (smart-campus/events/sensor)

## 1. Description
Dữ liệu cảm biến môi trường sau khi được IoT Ingestion Service (A1) tiếp nhận, kiểm tra schema, xác thực thiết bị và phân loại trạng thái.

## 2. Topic
`smart-campus/events/sensor`

## 3. Schema (JSON)
```json
{
  "event_id": "string (UUID)",
  "event_type": "sensor.reading.processed",
  "source_service": "iot-ingestion",
  "timestamp": "string (ISO 8601)",
  "raw_event_id": "string",
  "device_id": "string",
  "location": "string",
  "temperature_c": "number | null",
  "humidity_percent": "number | null",
  "motion_detected": "boolean",
  "light_lux": "number",
  "co2_ppm": "number",
  "smoke_ppm": "number",
  "battery_percent": "number",
  "status": "string (normal, warning, danger, sensor_error, invalid_device)",
  "alert_level": "string (none, low, medium, high)",
  "reason": "string"
}
```
