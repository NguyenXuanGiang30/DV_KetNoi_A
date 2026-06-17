# Hướng Dẫn Thiết Kế Hệ Thống Triển Khai & Cấu Hình Mạng LAN Radmin VPN

Thiết kế này nhằm mục đích đơn giản hóa việc triển khai thực tế trên mạng LAN ảo Radmin VPN cho dự án Smart Campus, giúp các nhóm dễ dàng liên kết bằng Radmin IP dạng `26.x.x.x`.

---

## 1. Kịch Bản Tạo Mạng Radmin VPN
Máy này đóng vai trò là **máy chính của khối**, có nhiệm vụ:
1. Tải và cài đặt phần mềm Radmin VPN.
2. Tạo một Network mới (ví dụ: `SmartCampus-BlockA-2026`) và thiết lập mật khẩu mạnh.
3. Chia sẻ tên mạng và mật khẩu cho các thành viên khác trong khối để họ kết nối vào.
4. Lấy IP Radmin của máy này (dải `26.x.x.x`) để chia sẻ cho các nhóm có dịch vụ liên kết chéo.

---

## 2. Kịch Bản Cấu Hình Firewall Tự Động
Hệ thống Windows Firewall mặc định chặn các truy cập ngoài LAN vào các cổng của các dịch vụ chạy trên Docker Host. Do đó, chúng ta cần cấu hình mở cổng tường lửa tự động cho các cổng từ `8001` đến `8007`.

### A. Tệp khởi chạy: `setup_firewall.bat`
* **Vị trí:** Thư mục gốc (`d:\BTL_DV_KetNoi\setup_firewall.bat`).
* **Vai trò:** Thực hiện gọi PowerShell để chạy script `.ps1` dưới quyền Quản trị (Administrator).
* **Nội dung:**
  ```bat
  @echo off
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0scratch\setup_firewall.ps1\"' -Verb RunAs"
  ```

### B. Tệp xử lý: `scratch/setup_firewall.ps1`
* **Vị trí:** `d:\BTL_DV_KetNoi\scratch\setup_firewall.ps1`.
* **Vai trò:** Xóa các rule cũ trùng tên và thêm các rule Firewall Inbound mới để cho phép truy cập qua cổng TCP `8001-8007`.
* **Nội dung:**
  * Kiểm tra quyền Admin, nếu chưa có thì yêu cầu nâng quyền.
  * Lặp qua mảng các cổng `8001` đến `8007` và thêm quy tắc vào Windows Firewall.

---

## 3. Công Cụ Cấu Hình IP Tương Tác: `scratch/configure_lan.py`
Tệp Python hỗ trợ người dùng xem IP và cập nhật file `.env` nhanh chóng mà không lo sợ sai cú pháp.

* **Vị trí:** `d:\BTL_DV_KetNoi\scratch\configure_lan.py`.
* **Quy trình hoạt động:**
  1. Đọc file `.env` hiện tại để parse các biến môi trường dạng `*_URL`.
  2. Quét tất cả các card mạng trên máy để lọc ra IP Radmin VPN (dải `26.x.x.x`) và các IP LAN khác để hiển thị cho người dùng biết IP của máy mình.
  3. Hiển thị menu cấu hình cho phép người dùng thay thế các URL dịch vụ đối tác bằng cách nhập IP Radmin của họ (ví dụ nhập `26.88.99.12` cho AI Vision, script tự lưu `AI_VISION_URL=http://26.88.99.12:8004`).
  4. Lưu cấu hình mới đè lại tệp `.env`.

---

## 4. Quy Trình Xác Minh Sau Triển Khai
Sau khi các máy đã ping thông đến nhau qua Radmin VPN:
1. Nhóm chạy docker-compose cho service được phân công:
   ```bash
   docker compose up -d --build <tên-service>
   ```
2. Gọi API `/health` của đối tác để đảm bảo thông luồng:
   ```bash
   curl http://<RADMIN_IP_ĐỐI_TÁC>:<PORT>/health
   ```
