# Smart Campus Operations Platform — Product A

Hệ thống giám sát và quản lý khuôn viên trường học thông minh gồm **7 microservice** giao tiếp qua **REST API** và **MQTT (HiveMQ)**.

## Kiến trúc

| Service | Port | Vai trò |
|---------|------|---------|
| A1: IoT Ingestion | 8001 | Thu thập, chuẩn hóa dữ liệu cảm biến |
| A2: Camera Stream | 8002 | Xử lý luồng camera, phát hiện chuyển động |
| A3: Access Gate | 8003 | Kiểm soát ra/vào bằng thẻ RFID |
| A4: AI Vision | 8004 | Nhận diện vật thể và đối chiếu khuôn mặt |
| A5: Analytics | 8005 | Tổng hợp và phân tích dữ liệu thống kê |
| A6: Core Business | 8006 | Xử lý nghiệp vụ trung tâm, policy engine |
| A7: Notification | 8007 | Gửi cảnh báo đa kênh |

## Yêu cầu

- Docker & Docker Compose
- Python 3.11+ (cho dev local)

## Khởi chạy nhanh

```bash
# 1. Copy file cấu hình
cp .env.example .env

# 2. Chỉnh sửa .env với thông tin thực tế (MQTT credentials, camera URL...)

# 3. Build & chạy tất cả service
docker compose up -d --build

# 4. Kiểm tra health
curl http://localhost:8001/health   # IoT Ingestion
curl http://localhost:8002/health   # Camera Stream
curl http://localhost:8003/health   # Access Gate
curl http://localhost:8004/health   # AI Vision
curl http://localhost:8005/health   # Analytics
curl http://localhost:8006/health   # Core Business
curl http://localhost:8007/health   # Notification

# 5. Xem log tất cả service
docker compose logs -f
```

## Ma trận Kết nối (10 cặp)

### REST Sync
| Consumer → Provider | Endpoint |
|-----|-----|
| Camera Stream → AI Vision | `POST /detect` |
| Core Business → AI Vision | `POST /vision/face-match` |
| Core Business → Access Gate | `GET /access/logs/recent` |
| Access Gate → Core Business | `POST /access/check` |

### MQTT Async (HiveMQ)
| Producer → Consumer | Topic |
|-----|-----|
| IoT Ingestion → Core, Analytics | `smart-campus/events/sensor` |
| Access Gate → Core, Analytics | `smart-campus/events/access` |
| Camera Stream → Analytics | `smart-campus/events/camera` |
| Core Business → Analytics, Notification | `smart-campus/events/core-alert` |

## Cấu trúc Dự án

```
services/
├── iot_ingestion/      # A1
├── camera_stream/      # A2
├── access_gate/        # A3
├── ai_vision/          # A4
├── analytics/          # A5
├── core_business/      # A6
└── notification/       # A7
```

Mỗi service chứa: `contracts/` (OpenAPI), `docs/`, `postman/`, `src/`, `Dockerfile`, `requirements.txt`.
