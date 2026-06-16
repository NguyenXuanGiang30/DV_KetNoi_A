# Event Contract: Camera Event (smart-campus/events/camera)

## 1. Description
Dữ liệu phát hiện chuyển động kèm kết quả phân tích hình ảnh từ AI Vision.

## 2. Topic
`smart-campus/events/camera`

## 3. Schema (JSON)
```json
{
  "event_id": "string",
  "event_type": "camera.vision.processed",
  "source_service": "camera-stream",
  "camera_id": "string",
  "timestamp": "string",
  "location": "string",
  "motion_detected": "boolean",
  "motion_score": "number",
  "detections": "array",
  "unknown_person": "boolean",
  "risk_level": "string"
}
```
