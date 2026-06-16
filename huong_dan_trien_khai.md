# Hướng Dẫn Chi Tiết Cấu Hình Và Cách Chạy Hệ Thống Smart Campus (Product A)

Tài liệu này cung cấp hướng dẫn chi tiết về ý nghĩa từng dòng cấu hình trong file `.env` và các bước khởi chạy cụ thể cho từng microservice bằng **Docker** hoặc **Python thuần (Uvicorn)**.

---

## I. GIẢI THÍCH CHI TIẾT CẤU HÌNH FILE `.env`

Khi chạy hệ thống, bạn cần copy file `.env.example` thành `.env` ở thư mục gốc của dự án. Dưới đây là ý nghĩa chi tiết của từng thông số cấu hình:

### 1. Cấu hình kết nối MQTT (HiveMQ Cloud)
Các dịch vụ truyền nhận dữ liệu cảm biến và sự kiện một cách bất đồng bộ thông qua Broker này.
*   `MQTT_BROKER_HOST`: Địa chỉ máy chủ MQTT của HiveMQ Cloud. Mặc định là máy chủ đám mây được cấu hình sẵn. Nếu các máy của bạn có mạng Internet thì **giữ nguyên**.
*   `MQTT_BROKER_PORT`: Cổng kết nối bảo mật SSL (mặc định là `8883`).
*   `MQTT_WS_PORT`: Cổng kết nối WebSockets (mặc định là `8884`).
*   `MQTT_IOT_USERNAME` / `MQTT_IOT_PASSWORD`: Tài khoản đăng nhập MQTT của dịch vụ IoT Ingestion (A1).
*   `MQTT_GATE_USERNAME` / `MQTT_GATE_PASSWORD`: Tài khoản đăng nhập MQTT của dịch vụ Access Gate (A3).

### 2. Cấu hình MQTT Topics
Các đường dẫn (chủ đề) để các dịch vụ gửi/nhận dữ liệu. **Giữ nguyên phần này**:
*   `TOPIC_RAW_IOT`: Nhận dữ liệu thô từ cảm biến môi trường.
*   `TOPIC_RAW_ACCESS`: Nhận dữ liệu mã thẻ RFID thô.
*   `TOPIC_EVENTS_SENSOR`: Gửi dữ liệu cảm biến sau khi đã chuẩn hóa.
*   `TOPIC_EVENTS_ACCESS`: Gửi dữ liệu quẹt thẻ sau khi đã xử lý.
*   `TOPIC_EVENTS_CAMERA`: Gửi sự kiện phân tích từ camera.
*   `TOPIC_EVENTS_CORE_ALERT`: Gửi cảnh báo từ hệ thống lõi.

### 3. Cấu hình cổng chạy dịch vụ (Service Ports)
Đây là các cổng mà các dịch vụ sẽ mở trên máy vật lý (máy Host) của bạn:
*   `IOT_INGESTION_PORT=8001` (Dịch vụ thu thập IoT)
*   `CAMERA_STREAM_PORT=8002` (Dịch vụ xử lý luồng camera)
*   `ACCESS_GATE_PORT=8003` (Dịch vụ kiểm soát cửa ra vào)
*   `AI_VISION_PORT=8004` (Dịch vụ nhận diện khuôn mặt/đối tượng)
*   `ANALYTICS_PORT=8005` (Dịch vụ thống kê dữ liệu)
*   `CORE_BUSINESS_PORT=8006` (Dịch vụ xử lý nghiệp vụ chính)
*   `NOTIFICATION_PORT=8007` (Dịch vụ gửi cảnh báo)

### 4. Cấu hình REST URLs (`*_URL`)
Đây là phần cấu hình **quan trọng nhất** quyết định việc chạy trên 1 máy hay nhiều máy khác nhau.

#### 👉 Trường hợp A: Chạy tất cả dịch vụ trên 1 máy duy nhất (Dùng Docker Compose)
Giữ nguyên tên dịch vụ làm hostname. Docker sẽ tự động điều hướng:
```ini
AI_VISION_URL=http://ai-vision:8000
ACCESS_GATE_URL=http://access-gate:8000
CORE_BUSINESS_URL=http://core-business:8000
ANALYTICS_URL=http://analytics:8000
NOTIFICATION_URL=http://notification:8000
```
*(Lưu ý: Bên trong mạng Docker ảo, các container nói chuyện trực tiếp qua cổng mặc định `8000` của chúng).*

#### 👉 Trường hợp B: Chạy phân tán trên nhiều máy trong mạng LAN (Hoặc chạy ngoài Docker)
Bạn phải thay thế các tên dịch vụ ảo bằng **IP mạng LAN** của máy đang chạy dịch vụ đó và **Port tương ứng của máy Host** (từ `8001` đến `8007`).

*Giả sử:*
*   Máy chạy AI Vision (A4) có IP LAN là `192.168.1.20`
*   Máy chạy Access Gate (A3) có IP LAN là `192.168.1.30`
*   Máy chạy Core Business (A6) có IP LAN là `192.168.1.10`
*   Máy chạy Analytics (A5) có IP LAN là `192.168.1.30`
*   Máy chạy Notification (A7) có IP LAN là `192.168.1.30`

Cấu hình `.env` trên **TẤT CẢ các máy** phải được cập nhật đồng loạt thành:
```ini
AI_VISION_URL=http://192.168.1.20:8004
ACCESS_GATE_URL=http://192.168.1.30:8003
CORE_BUSINESS_URL=http://192.168.1.10:8006
ANALYTICS_URL=http://192.168.1.30:8005
NOTIFICATION_URL=http://192.168.1.30:8007
```

---

## II. HƯỚNG DẪN CHI TIẾT CÁCH CHẠY HỆ THỐNG

### Cách 1: Khởi chạy bằng Docker (Được khuyên dùng nhất)
*Yêu cầu: Đã cài đặt Docker Desktop (Windows/macOS) hoặc Docker Engine (Linux).*

#### 1. Khởi chạy toàn bộ dịch vụ trên cùng một máy:
Mở terminal tại thư mục gốc chứa file `docker-compose.yml` và chạy:
```bash
docker compose up -d --build
```

#### 2. Khởi chạy chọn lọc từng dịch vụ trên các máy LAN khác nhau:
Bạn copy toàn bộ thư mục code sang các máy. Ở mỗi máy, sau khi cấu hình file `.env` tương ứng, chạy lệnh khởi động đúng dịch vụ được phân công:
*   **Trên máy chạy AI Vision:**
    ```bash
    docker compose up -d --build ai-vision
    ```
*   **Trên máy chạy Core Business:**
    ```bash
    docker compose up -d --build core-business
    ```
*   **Trên máy chạy Access Gate:**
    ```bash
    docker compose up -d --build access-gate
    ```

#### 3. Các lệnh Docker hữu ích để quản lý:
*   Xem danh sách các dịch vụ đang chạy: `docker compose ps`
*   Xem log (nhật ký) thời gian thực của toàn bộ hệ thống: `docker compose logs -f`
*   Xem log của một dịch vụ cụ thể: `docker compose logs -f ai-vision`
*   Dừng toàn bộ hệ thống: `docker compose down`

---

### Cách 2: Khởi chạy thủ công bằng Python thuần (Không dùng Docker)
*Yêu cầu: Máy tính đã cài đặt Python 3.11 trở lên.*

Nếu chạy bằng Python, bạn cần làm các bước sau trên máy chạy dịch vụ đó:

#### Bước 1: Tạo môi trường ảo (Virtual Environment - Khuyên dùng để tránh xung đột thư viện)
Mở terminal tại thư mục gốc dự án và chạy:
```bash
# Tạo môi trường ảo tên là venv
python -m venv venv

# Kích hoạt môi trường ảo:
# Trên Windows:
venv\Scripts\activate
# Trên macOS / Linux:
source venv/bin/activate
```

#### Bước 2: Cài đặt thư viện của dịch vụ cần chạy
Mỗi dịch vụ sẽ có file `requirements.txt` riêng. Di chuyển vào thư mục dịch vụ và cài đặt:
```bash
pip install -r services/<tên_thư_mục_dịch_vụ>/requirements.txt
```

#### Bước 3: Khởi chạy từng dịch vụ bằng Uvicorn
Chạy lệnh uvicorn từ thư mục gốc của dự án. 
> [!IMPORTANT]
> Lưu ý quan trọng: Bắt buộc phải có tham số `--host 0.0.0.0` để dịch vụ chấp nhận các kết nối đi từ IP khác trong mạng LAN. Cổng `--port` phải đặt đúng theo cổng máy host được định nghĩa trong file `.env`.

*   **Chạy dịch vụ A1 (IoT Ingestion) ở cổng 8001:**
    ```bash
    uvicorn main:app --app-dir services/iot_ingestion/src --host 0.0.0.0 --port 8001
    ```
*   **Chạy dịch vụ A2 (Camera Stream) ở cổng 8002:**
    ```bash
    uvicorn main:app --app-dir services/camera_stream/src --host 0.0.0.0 --port 8002
    ```
*   **Chạy dịch vụ A3 (Access Gate) ở cổng 8003:**
    ```bash
    uvicorn main:app --app-dir services/access_gate/src --host 0.0.0.0 --port 8003
    ```
*   **Chạy dịch vụ A4 (AI Vision) ở cổng 8004:**
    ```bash
    uvicorn main:app --app-dir services/ai_vision/src --host 0.0.0.0 --port 8004
    ```
*   **Chạy dịch vụ A5 (Analytics) ở cổng 8005:**
    ```bash
    uvicorn main:app --app-dir services/analytics/src --host 0.0.0.0 --port 8005
    ```
*   **Chạy dịch vụ A6 (Core Business) ở cổng 8006:**
    ```bash
    uvicorn main:app --app-dir services/core_business/src --host 0.0.0.0 --port 8006
    ```
*   **Chạy dịch vụ A7 (Notification) ở cổng 8007:**
    ```bash
    uvicorn main:app --app-dir services/notification/src --host 0.0.0.0 --port 8007
    ```

---

## III. CÁCH KIỂM TRA HỆ THỐNG SAU KHI CHẠY

Để kiểm tra xem các dịch vụ trên các máy khác nhau có thực sự liên kết tốt với nhau không, bạn có thể thực hiện kiểm tra như sau:

1.  **Kiểm tra qua API Health**:
    Từ bất kỳ máy nào trong mạng LAN, mở trình duyệt web hoặc dùng Postman truy cập đường dẫn:
    `http://<IP_MÁY_CHẠY>:<CỔNG_DỊCH_VỤ>/health`
    *Ví dụ:* Truy cập `http://192.168.1.20:8004/health` để xem dịch vụ AI Vision của Máy B có đang hoạt động tốt không. Kết quả trả về phải có định dạng JSON: `{"status": "ok", ...}`.
2.  **Kiểm tra tính liên thông**:
    Khi bạn thực hiện quẹt thẻ tại cổng `Access Gate` (chạy trên Máy C), nó sẽ gửi một yêu cầu `POST /access/check` tới `Core Business` (chạy trên Máy A). Hãy kiểm tra log terminal của Máy A (chạy Core Business) xem có xuất hiện dòng thông tin xử lý sự kiện quẹt thẻ đó hay không.
