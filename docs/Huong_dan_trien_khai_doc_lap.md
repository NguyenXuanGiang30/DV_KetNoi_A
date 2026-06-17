# Hướng Dẫn Triển Khai Độc Lập Cho Từng Nhóm Trong Khối

Tài liệu này hướng dẫn chi tiết lệnh chạy Docker và các biến `.env` bắt buộc phải cấu hình cho từng nhóm (từ A1 đến A7) khi triển khai độc lập trên máy demo riêng của nhóm mình.

---

## Quy Trình Chung Cho Tất Cả Các Nhóm
Trước khi chạy lệnh của nhóm mình, tất cả các máy demo cần thực hiện:
1. Kết nối vào mạng **Radmin VPN** chung của khối.
2. Nhấp đúp chạy file `setup_firewall.bat` ở thư mục gốc để mở cổng Firewall.
3. Tạo file `.env` từ file `.env.example` và cập nhật thông tin mạng.

---

## Chi Tiết Triển Khai Cho Từng Nhóm

### Nhóm A1: IoT Ingestion (Cổng 8001)
* **Lệnh chạy:**
  ```bash
  docker compose up -d --build iot-ingestion
  ```
* **Cấu hình `.env` bắt buộc:**
  * Nhóm A1 chỉ cần kết nối MQTT nên cần điền đúng tài khoản HiveMQ:
    ```ini
    MQTT_BROKER_HOST=f6f78e87db4a4c189dd3d706745a5e93.s1.eu.hivemq.cloud
    MQTT_IOT_USERNAME=DVKN_IOT_2026
    MQTT_IOT_PASSWORD=ThaiBao12A@
    ```

---

### Nhóm A2: Camera Stream (Cổng 8002)
* **Lệnh chạy:**
  * *Chạy qua Docker (Nếu dùng luồng video RTSP/HTTP):*
    ```bash
    docker compose up -d --build camera-stream
    ```
  * *Chạy qua Python trực tiếp (Nếu cần dùng Webcam laptop ngoài Docker):*
    ```bash
    pip install -r services/camera_stream/requirements.txt
    python services/camera_stream/src/main.py
    ```
* **Cấu hình `.env` bắt buộc:**
  * Nhóm A2 cần gọi sang AI Vision (A4) để phát hiện vật thể/khuôn mặt:
    ```ini
    # Điền Radmin IP của máy chạy AI Vision (A4)
    AI_VISION_URL=http://<IP_RADMIN_NHOM_A4>:8004
    ```

---

### Nhóm A3: Access Gate (Cổng 8003)
* **Lệnh chạy:**
  ```bash
  docker compose up -d --build access-gate
  ```
* **Cấu hình `.env` bắt buộc:**
  * Nhóm A3 cần kết nối MQTT (để nhận tín hiệu quẹt thẻ) và gọi sang Core Business (A6) để check quyền ra vào:
    ```ini
    MQTT_BROKER_HOST=f6f78e87db4a4c189dd3d706745a5e93.s1.eu.hivemq.cloud
    MQTT_GATE_USERNAME=DVKN2026
    MQTT_GATE_PASSWORD=ThaiBao12A@
    
    # Điền Radmin IP của máy chạy Core Business (A6)
    CORE_BUSINESS_URL=http://<IP_RADMIN_NHOM_A6>:8006
    ```

---

### Nhóm A4: AI Vision (Cổng 8004)
* **Lệnh chạy:**
  ```bash
  docker compose up -d --build ai-vision
  ```
* **Cấu hình `.env` bắt buộc:**
  * Nhóm A4 là dịch vụ cung cấp API xử lý ảnh, chỉ cần chạy đúng cổng và cấp IP Radmin của mình cho nhóm A2 và A6. Không cần cấu hình gọi các dịch vụ khác.

---

### Nhóm A5: Analytics (Cổng 8005)
* **Lệnh chạy:**
  ```bash
  docker compose up -d --build analytics
  ```
* **Cấu hình `.env` bắt buộc:**
  * Nhóm A5 chỉ lắng nghe sự kiện từ MQTT để thống kê, do đó cần điền đúng thông tin HiveMQ MQTT Broker.

---

### Nhóm A6: Core Business (Cổng 8006)
* **Lệnh chạy:**
  ```bash
  docker compose up -d --build core-business
  ```
* **Cấu hình `.env` bắt buộc:**
  * Nhóm A6 là dịch vụ trung tâm xử lý nghiệp vụ, cần gọi đến AI Vision (A4) và Access Gate (A3):
    ```ini
    # Điền Radmin IP của máy chạy AI Vision (A4)
    AI_VISION_URL=http://<IP_RADMIN_NHOM_A4>:8004
    
    # Điền Radmin IP của máy chạy Access Gate (A3)
    ACCESS_GATE_URL=http://<IP_RADMIN_NHOM_A3>:8003
    ```

---

### Nhóm A7: Notification (Cổng 8007)
* **Lệnh chạy:**
  ```bash
  docker compose up -d --build notification
  ```
* **Cấu hình `.env` bắt buộc:**
  * Nhóm A7 nhận cảnh báo từ MQTT và gửi qua Telegram/Email thật:
    ```ini
    # Cấu hình Token Telegram nhận từ BotFather
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    TELEGRAM_CHAT_ID=your_chat_id
    
    # Cấu hình SMTP Email (Ví dụ Gmail)
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=your_email@gmail.com
    SMTP_PASSWORD=your_app_password
    SMTP_RECEIVER=receiver_email@gmail.com
    ```

---

## Lệnh Kiểm Tra Kết Nối Giữa Các Máy
Để kiểm tra xem máy nhóm mình đã thông và gọi được dịch vụ của nhóm đối tác hay chưa, hãy sử dụng lệnh `curl` từ Terminal/PowerShell:

```bash
# Kiểm tra kết nối tới AI Vision của nhóm A4:
curl http://<IP_RADMIN_NHOM_A4>:8004/health

# Kiểm tra kết nối tới Core Business của nhóm A6:
curl http://<IP_RADMIN_NHOM_A6>:8006/health
```

*Nếu trả về `HTTP 200` hoặc dữ liệu JSON thành công tức là kết nối đã hoàn toàn thông suốt.*
