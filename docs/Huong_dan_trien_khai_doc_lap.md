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

### Bước 4: Khởi chạy dịch vụ của riêng nhóm mình
Đảm bảo phần mềm **Docker Desktop** đã được mở và đang chạy ngầm trên máy của bạn.
Chọn lệnh tương ứng với nhóm của bạn và gõ vào Terminal để chạy:

| Nhóm | Tên Dịch Vụ | Cổng REST | Lệnh Chạy Qua Docker |
|---|---|---|---|
| **A1** | IoT Ingestion | `8001` | `docker compose up -d --build iot-ingestion` |
| **A2** | Camera Stream | `8002` | `docker compose up -d --build camera-stream` |
| **A3** | Access Gate | `8003` | `docker compose up -d --build access-gate` |
| **A4** | AI Vision | `8004` | `docker compose up -d --build ai-vision` |
| **A5** | Analytics | `8005` | `docker compose up -d --build analytics` |
| **A6** | Core Business | `8006` | `docker compose up -d --build core-business` |
| **A7** | Notification | `8007` | `docker compose up -d --build notification` |

*(Tham số `-d` giúp container chạy ngầm dưới nền).*

> [!TIP]
> **Đối với Nhóm A2 (Camera Stream):** Do container Docker không thể trực tiếp truy cập Webcam vật lý của Laptop nếu không cấu hình thêm driver phức tạp, khuyến nghị nhóm A2 chạy trực tiếp bằng Python trên máy Host:
> 1. Mở PowerShell trong thư mục dự án và chạy:
>    ```bash
>    pip install -r services/camera_stream/requirements.txt
>    python services/camera_stream/src/main.py
>    ```

---

## PHẦN 3: KIỂM TRA & GIÁM SÁT DỊCH VỤ

### 1. Xem nhật ký hoạt động (Logs) của Container
Để biết dịch vụ có bị lỗi gì không hoặc xem dữ liệu đang được truyền nhận như thế nào:
```bash
# Định dạng: docker compose logs -f <tên-dịch-vụ>
# Ví dụ nhóm A3 muốn xem log của Access Gate:
docker compose logs -f access-gate
```
*(Nhấn `Ctrl + C` để thoát màn hình xem log).*

### 2. Kiểm tra Healthcheck dịch vụ của đối tác
Khi các nhóm đã chạy thành công, hãy kiểm tra xem mạng LAN Radmin có kết nối thông suốt chưa bằng cách gọi API Healthcheck:
```bash
# Mở PowerShell/CMD và gõ (thay IP đối tác):
curl http://<IP_RADMIN_ĐỐI_TÁC>:<CỔNG_DỊCH_VỤ>/health

# Ví dụ kiểm tra xem máy của nhóm A4 (AI Vision) có nhận được kết nối từ bạn không:
curl http://26.115.42.99:8004/health
```
Nếu màn hình trả về kết quả dạng: `{"status":"ok", ...}` hoặc `{"status":"healthy", ...}` thì chúc mừng, kết nối giữa hai máy đã hoàn tất thành công!
