# Event Contract: Access Event (smart-campus/events/access)

## 1. Description
Dữ liệu quẹt thẻ ra/vào sau khi được Access Gate Service (A3) đối chiếu whitelist.

## 2. Topic
`smart-campus/events/access`

## 3. Schema (JSON)
```json
{
  "event_id": "string",
  "event_type": "access.swipe.processed",
  "source_service": "access-gate",
  "timestamp": "string (ISO 8601)",
  "raw_event_id": "string",
  "uid": "string",
  "student_id": "string | null",
  "full_name": "string | null",
  "class_name": "string | null",
  "door_id": "string",
  "location": "string",
  "direction": "string (in/out)",
  "access_result": "string (granted/denied)",
  "reason": "string"
}
```
