# Event Contract: Core Alert (smart-campus/events/core-alert)

## 1. Description
Cảnh báo hệ thống được sinh ra bởi Core Business Service sau khi đối chiếu policy nghiệp vụ.

## 2. Topic
`smart-campus/events/core-alert`

## 3. Schema (JSON)
```json
{
  "id": "string",
  "source_service": "core-business",
  "alert_type": "string",
  "severity": "string (LOW, MEDIUM, HIGH, CRITICAL)",
  "message": "string",
  "related_event_id": "string | null",
  "status": "string (OPEN, RESOLVED)",
  "created_at": "string",
  "resolved_at": "string | null"
}
```
