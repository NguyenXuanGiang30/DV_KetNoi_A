# HƯỚNG DẪN CÀI ĐẶT & TRIỂN KHAI CHI TIẾT TỪNG NHÓM (MÔI TRƯỜNG LAN/RADMIN)

Tài liệu này cung cấp hướng dẫn cài đặt từng bước, từ việc chuẩn bị phần mềm đến chạy dịch vụ độc lập trên máy tính của từng nhóm. Vui lòng thực hiện tuần tự để tránh lỗi kết nối.

---

## PHẦN 1: CÁC PHẦN MỀM BẮT BUỘC PHẢI CÀI ĐẶT (PREREQUISITES)

Mỗi máy tính chạy dịch vụ của nhóm cần cài đặt đầy đủ các công cụ sau:

### 1. Docker Desktop (Bắt buộc để chạy Container)
Dịch vụ của các nhóm được đóng gói bằng Docker.
*   **Tải về:** Truy cập trang chủ [Docker Desktop](https://www.docker.com/products/docker-desktop/) và tải bản cài đặt tương ứng với hệ điều hành (Windows/macOS).
*   **Lưu ý khi cài trên Windows:**
    *   Trong quá trình cài đặt, chọn tích hợp **WSL 2** (được khuyến nghị) thay vì Hyper-V.
    *   Sau khi cài xong, bạn **phải khởi động lại máy tính**.
    *   **Quan trọng:** Trước khi chạy lệnh deploy, hãy bật ứng dụng Docker Desktop lên và đảm bảo biểu tượng Docker ở góc dưới bên trái có màu xanh lá cây (đang chạy).

### 2. Python (Phiên bản 3.10 hoặc cao hơn)
Cần thiết để chạy script mở tường lửa, cấu hình IP tự động và kiểm thử kết nối.
*   **Tải về:** Truy cập [Python.org Downloads](https://www.python.org/downloads/) và tải phiên bản mới nhất.
*   **Lưu ý QUAN TRỌNG khi cài đặt trên Windows:**
    *   Ở màn hình đầu tiên của bộ cài đặt, bắt buộc phải tích chọn ô **"Add python.exe to PATH"** (nếu không tích, bạn sẽ không chạy được lệnh `python` từ terminal).
*   **Kiểm tra:** Mở Terminal (Command Prompt hoặc PowerShell) và gõ lệnh sau để kiểm tra:
    ```bash
    python --version
    ```
    *Nếu hiện ra dạng `Python 3.10.x` hoặc `3.11.x` hoặc `3.12.x` là thành công.*

### 3. Radmin VPN (Để kết nối mạng LAN ảo từ xa)
Giúp máy tính của các nhóm nhìn thấy nhau như trong mạng LAN cục bộ.
*   **Tải về:** Truy cập [Radmin VPN](https://www.radmin-vpn.com/) (chỉ hỗ trợ Windows) và tải về cài đặt.
*   **Quy trình kết nối:**
    *   **Máy Trưởng khối:** Bật Radmin VPN -> Chọn **Mạng (Network)** -> **Tạo mạng mới (Create new network)** -> Đặt tên mạng và mật khẩu, rồi gửi thông tin này cho các nhóm thành viên.
    *   **Máy các Nhóm khác (Thành viên):** Bật Radmin VPN -> Chọn **Mạng (Network)** -> **Tham gia mạng đã có (Join an existing network)** -> Điền tên mạng và mật khẩu trưởng khối đã gửi để tham gia.
    *   **Xác nhận:** Khi đã tham gia thành công, bạn sẽ thấy danh sách máy tính của các nhóm khác sáng xanh. Địa chỉ IP của bạn sẽ có dạng `26.x.x.x` hiển thị to rõ ở giao diện chính Radmin VPN.

### 4. Git (Để tải mã nguồn)
*   **Tải về:** Truy cập [Git cho Windows](https://git-scm.com/download/win) và tải về cài đặt (chọn cấu hình mặc định).

---

## PHẦN 2: QUY TRÌNH TRIỂN KHAI TỪNG BƯỚC (STEP-BY-STEP)

Sau khi cài đặt xong các phần mềm ở **Phần 1**, hãy làm theo các bước dưới đây để chạy dịch vụ của nhóm mình:

### Bước 1: Đồng bộ mã nguồn từ Git về máy
1. Mở Terminal (Command Prompt/PowerShell) và di chuyển vào thư mục dự án của bạn.
2. Chuyển sang nhánh chứa công cụ LAN (`deploy-lan`):
   ```bash
   git checkout deploy-lan
   git pull origin deploy-lan
   ```

### Bước 2: Mở Windows Firewall tự động
Tường lửa Windows mặc định sẽ chặn các máy khác gọi API vào cổng dịch vụ của bạn.
1. Tìm tệp tin **`setup_firewall.bat`** ở thư mục gốc của dự án.
2. Nhấp chuột phải vào tệp và chọn **Run as Administrator** (hoặc nhấp đúp chuột trái trực tiếp).
3. Một cửa sổ đen (hoặc xanh của PowerShell) sẽ hiện ra hỏi quyền quản trị -> Chọn **Yes**.
4. Script sẽ tự động thực thi và mở các cổng từ `8001` đến `8007`. Nhấn phím bất kỳ để đóng cửa sổ khi hoàn tất.

### Bước 3: Tạo tệp cấu hình `.env` & Chạy công cụ chỉnh IP
1. Tại thư mục gốc của dự án, sao chép tệp `.env.example` thành tệp `.env`:
   * **Lệnh chạy nhanh trên Windows (PowerShell):**
     ```powershell
     copy .env.example .env
     ```
2. Chạy công cụ cấu hình IP tương tác:
   ```bash
   python scratch/configure_lan.py
   ```
3. **Màn hình giao diện công cụ:**
   * Dòng đầu tiên sẽ thông báo địa chỉ IP Radmin của bạn (dạng `26.x.x.x`). Hãy sao chép IP này gửi cho các nhóm khác cần gọi đến dịch vụ của bạn.
   * Danh sách 7 dịch vụ sẽ hiện ra.
   * Để đổi IP của dịch vụ đối tác mà bạn cần gọi, hãy chọn số tương ứng (1-7), sau đó nhập địa chỉ IP Radmin của đối tác đó.
   * Chọn số **`8`** để lưu cấu hình và thoát.

### Bước 4: Hướng dẫn chi tiết riêng cho TỪNG MÁY / TỪNG NHÓM

Mỗi nhóm hãy tìm đến đúng mục của nhóm mình dưới đây để cấu hình và chạy:

---

### MÁY NHÓM A1: IoT Ingestion (Cổng 8001)
* **Nhiệm vụ:** Nhận dữ liệu nhiệt độ, độ ẩm, CO2 từ các cảm biến IoT và đẩy lên cơ sở dữ liệu/Hệ thống trung tâm.
* **Các bước thực hiện trên Máy A1:**
  1. Tạo file `.env` và điền thông tin MQTT Broker của HiveMQ Cloud.
  2. Bật ứng dụng **Docker Desktop**.
  3. Mở Terminal tại thư mục gốc của dự án và chạy duy nhất container của nhóm A1:
     ```bash
     docker compose up -d --build iot-ingestion
     ```
  4. **Cách kiểm tra logs (Xem dữ liệu chạy):**
     ```bash
     docker compose logs -f iot-ingestion
     ```
  5. **Xác nhận hoạt động:** Mở trình duyệt web hoặc PowerShell trên máy bất kỳ và gọi:
     ```bash
     curl http://<IP_RADMIN_MÁY_A1>:8001/health
     ```
     *(Phải trả về JSON chứa `"status": "healthy"` hoặc `"status": "ok"`).*

---

### MÁY NHÓM A2: Camera Stream (Cổng 8002)
* **Nhiệm vụ:** Stream hình ảnh từ Webcam/Camera, gửi ảnh đến AI Vision (A4) để nhận diện khuôn mặt và phát hiện hành vi.
* **Các bước thực hiện trên Máy A2:**
  1. Hỏi nhóm A4 địa chỉ IP Radmin của máy họ (ví dụ: `26.111.222.33`).
  2. Chạy `python scratch/configure_lan.py`, chọn dịch vụ số **`4` (AI_VISION_URL)** và nhập IP Radmin của máy A4 vừa lấy.
  3. **Cách chạy khuyến nghị (Chạy trực tiếp trên Host để bắt được Camera/Webcam):**
     * Cài đặt thư viện Python:
       ```bash
       pip install -r services/camera_stream/requirements.txt
       ```
     * Khởi chạy code Camera:
       ```bash
       python services/camera_stream/src/main.py
       ```
  4. **Cách chạy qua Docker (Chỉ dùng nếu stream từ link video tĩnh/không dùng Webcam):**
     ```bash
     docker compose up -d --build camera-stream
     ```
  5. **Xác nhận hoạt động:** Từ máy bất kỳ gọi:
     ```bash
     curl http://<IP_RADMIN_MÁY_A2>:8002/health
     ```

---

### MÁY NHÓM A3: Access Gate (Cổng 8003)
* **Nhiệm vụ:** Kiểm soát cửa ra vào bằng thẻ RFID/Mã số. Gửi yêu cầu check thẻ sang Core Business (A6) để quyết định đóng/mở cửa.
* **Các bước thực hiện trên Máy A3:**
  1. Hỏi nhóm A6 địa chỉ IP Radmin của máy họ (ví dụ: `26.111.222.44`).
  2. Chạy `python scratch/configure_lan.py`, chọn dịch vụ số **`6` (CORE_BUSINESS_URL)** và nhập IP Radmin của máy A6.
  3. Bật ứng dụng **Docker Desktop**.
  4. Khởi chạy duy nhất container của nhóm A3:
     ```bash
     docker compose up -d --build access-gate
     ```
  5. **Cách kiểm tra logs (Xem quẹt thẻ thành công/thất bại):**
     ```bash
     docker compose logs -f access-gate
     ```
  6. **Xác nhận hoạt động:** Từ máy bất kỳ gọi:
     ```bash
     curl http://<IP_RADMIN_MÁY_A3>:8003/health
     ```

---

### MÁY NHÓM A4: AI Vision (Cổng 8004)
* **Nhiệm vụ:** Cung cấp API nhận diện khuôn mặt và phát hiện vật thể/con người (yolo) cho nhóm A2 và A6 gọi tới.
* **Các bước thực hiện trên Máy A4:**
  1. Lấy IP Radmin của máy mình (Ví dụ: `26.111.222.33`) gửi cho nhóm A2 và A6.
  2. Bật ứng dụng **Docker Desktop**.
  3. Khởi chạy duy nhất container của nhóm A4:
     ```bash
     docker compose up -d --build ai-vision
     ```
  4. **Cách kiểm tra logs:**
     ```bash
     docker compose logs -f ai-vision
     ```
  5. **Xác nhận hoạt động:** Từ máy bất kỳ gọi:
     ```bash
     curl http://<IP_RADMIN_MÁY_A4>:8004/health
     ```

---

### MÁY NHÓM A5: Analytics (Cổng 8005)
* **Nhiệm vụ:** Tổng hợp dữ liệu cảm biến, lượt ra vào cửa, số lượng người phát hiện được để vẽ biểu đồ Dashboard.
* **Các bước thực hiện trên Máy A5:**
  1. Tạo file `.env` và điền thông tin MQTT Broker của HiveMQ Cloud.
  2. Bật ứng dụng **Docker Desktop**.
  3. Khởi chạy duy nhất container của nhóm A5:
     ```bash
     docker compose up -d --build analytics
     ```
  4. **Cách kiểm tra logs:**
     ```bash
     docker compose logs -f analytics
     ```
  5. **Xác nhận hoạt động:** Từ máy bất kỳ gọi:
     ```bash
     curl http://<IP_RADMIN_MÁY_A5>:8005/health
     ```

---

### MÁY NHÓM A6: Core Business (Cổng 8006)
* **Nhiệm vụ:** Bộ não trung tâm. Khi A3 gửi yêu cầu quẹt thẻ, A6 sẽ gọi sang A4 (AI Vision) khớp khuôn mặt và gọi A3 (Access Gate) lấy log cũ để ra quyết định đóng/mở cửa.
* **Các bước thực hiện trên Máy A6:**
  1. Hỏi nhóm A3 và nhóm A4 địa chỉ IP Radmin của họ.
  2. Chạy `python scratch/configure_lan.py`:
     * Chọn dịch vụ số **`3` (ACCESS_GATE_URL)** và nhập IP Radmin của máy A3.
     * Chọn dịch vụ số **`4` (AI_VISION_URL)** và nhập IP Radmin của máy A4.
  3. Bật ứng dụng **Docker Desktop**.
  4. Khởi chạy duy nhất container của nhóm A6:
     ```bash
     docker compose up -d --build core-business
     ```
  5. **Cách kiểm tra logs (Xem luồng xử lý nghiệp vụ):**
     ```bash
     docker compose logs -f core-business
     ```
  6. **Xác nhận hoạt động:** Từ máy bất kỳ gọi:
     ```bash
     curl http://<IP_RADMIN_MÁY_A6>:8006/health
     ```

---

### MÁY NHÓM A7: Notification (Cổng 8007)
* **Nhiệm vụ:** Nhận tin nhắn cảnh báo từ MQTT và thực hiện gửi thông báo thật qua Telegram Bot hoặc SMTP Email.
* **Các bước thực hiện trên Máy A7:**
  1. Mở file `.env` và cấu hình các thông số thật cho Telegram (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) hoặc Email (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_RECEIVER`).
  2. Bật ứng dụng **Docker Desktop**.
  3. Khởi chạy duy nhất container của nhóm A7:
     ```bash
     docker compose up -d --build notification
     ```
  4. **Cách kiểm tra logs (Xem tin nhắn đã gửi đi chưa):**
     ```bash
     docker compose logs -f notification
     ```
  5. **Xác nhận hoạt động:** Từ máy bất kỳ gọi:
     ```bash
     curl http://<IP_RADMIN_MÁY_A7>:8007/health
     ```

---

## PHẦN 4: HƯỚNG DẪN XỬ LÝ LỖI NHANH (TROUBLESHOOTING)

*   **Lỗi: `Connection Refused` hoặc không gọi được sang máy đối tác:**
    *   *Khắc phục:* Kiểm tra xem đối tác đã bật Radmin VPN chưa, đã chạy file `setup_firewall.bat` để mở tường lửa chưa. Cả hai máy phải PING được IP Radmin của nhau mới kết nối được.
*   **Lỗi: `docker: command not found`:**
    *   *Khắc phục:* Bạn chưa cài Docker Desktop hoặc chưa thêm Docker vào biến môi trường PATH. Khởi động lại máy hoặc cài đặt lại theo Phần 1.
*   **Lỗi: `Port already in use`:**
    *   *Khắc phục:* Cổng dịch vụ đang bị chiếm dụng bởi một tiến trình khác trên máy bạn. Hãy tắt tiến trình đó đi hoặc restart máy tính để giải phóng cổng.

