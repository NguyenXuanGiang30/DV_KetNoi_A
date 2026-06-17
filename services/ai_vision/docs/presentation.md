# Hướng Dẫn Trình Bày Demo — A4: AI Vision Service

Bản tài liệu này hướng dẫn chi tiết kịch bản thuyết trình và bảo vệ đồ án tích hợp hệ thống cho nhóm phụ trách dịch vụ **AI Vision Service (A4)** theo quy trình 6 bước chuẩn.

---

## 1. Vai trò của nhóm
* **Tên dịch vụ:** AI Vision Service (A4).
* **Vai trò trong hệ thống Smart Campus:**
  * Cung cấp dịch vụ trí tuệ nhân tạo chuyên biệt để phân tích hình ảnh và nhận diện khuôn mặt.
  * Hỗ trợ nhận diện các loại vật thể chuyển động (người, phương tiện) từ các góc camera giám sát.
  * Hỗ trợ so sánh khớp khuôn mặt (Face Matching) để phục vụ kiểm soát an ninh cửa ra vào.
* **Mô hình giao tiếp:** Hoạt động với vai trò thuần **REST Provider** (cung cấp API dịch vụ đồng bộ).

---

## 2. Input
* **Dữ liệu nhận:** Request JSON đồng bộ qua giao thức HTTP POST chứa ảnh đầu vào:
  * API `/detect`:
    ```json
    {
      "camera_id": "CAM-HALLWAY-01",
      "image_url": "https://smart-campus.local/storage/cam01_t1.jpg",
      "image_base64": null,
      "timestamp": "2026-06-17T02:30:10Z",
      "motion_score": 0.76
    }
    ```
  * API `/vision/face-match`:
    ```json
    {
      "camera_id": "DOOR-CAM-01",
      "image_url": "https://smart-campus.local/storage/door01_t1.jpg",
      "reference_face_id": "FACE-DNU-12345",
      "timestamp": "2026-06-17T02:30:10Z"
    }
    ```
* **Nguồn gửi:** Camera Stream Service (gọi `/detect` để phát hiện vật thể) và Core Business Service (gọi `/vision/face-match` để đối chiếu khuôn mặt ra vào).
* **Giao thức:** REST HTTP POST (Header bắt buộc chứa `Authorization: Bearer <AUTH_TOKEN>`).

---

## 3. Xử lý nghiệp vụ
* **Xác thực Token bảo mật:** Kiểm tra Header `Authorization`. Nếu token trống hoặc không khớp với mã dùng chung `smart-campus-dev-token-2026`, từ chối xử lý và trả về mã lỗi HTTP 401.
* **Kiểm tra dữ liệu ảnh:** Đảm bảo request phải cung cấp ít nhất một trong hai trường `image_url` hoặc `image_base64`. Nếu không có, từ chối và trả về lỗi HTTP 400.
* **Mô phỏng mô hình AI (AI Inference Simulator):**
  * Đối với `/detect`: Tạo ngẫu nhiên danh sách vật thể nhận diện (nhãn: `person`, `vehicle`, `unknown`), tính tọa độ bounding box `bbox` và gán mức độ tin cậy ngẫu nhiên (từ 0.70 đến 0.99). Đồng thời tính toán mức độ nguy hiểm (`risk_level: high` nếu phát hiện nhãn `unknown`).
  * Đối với `/vision/face-match`: Thực hiện thuật toán so khớp khoảng cách vector để so sánh khuôn mặt trong ảnh với khuôn mặt gốc `reference_face_id`, trả về kết quả khớp (`matched: true/false`).

---

## 4. Output
* **Dữ liệu trả ra:** Phản hồi JSON chứa thông tin nhận dạng chi tiết:
  * Kết quả `/detect` (HTTP 200 OK):
    ```json
    {
      "detection_id": "det-12345678",
      "camera_id": "CAM-HALLWAY-01",
      "timestamp": "2026-06-17T02:30:10Z",
      "detections": [
        {
          "label": "person",
          "confidence": 0.94,
          "bbox": [100, 150, 300, 450],
          "risk_level": "medium"
        }
      ],
      "unknown_person": false,
      "risk_level": "medium"
    }
    ```
  * Kết quả `/vision/face-match` (HTTP 200 OK):
    ```json
    {
      "match_id": "match-87654321",
      "camera_id": "DOOR-CAM-01",
      "matched": true,
      "confidence": 0.96,
      "timestamp": "2026-06-17T02:30:10Z"
    }
    ```

---

## 5. Output gửi cho ai?
* **Bên nhận:** Trả trực tiếp trong HTTP Response đồng bộ cho client đã gọi yêu cầu:
  * Trả về cho **Camera Stream (A2)** đối với yêu cầu phân tích vật thể.
  * Trả về cho **Core Business (A6)** đối với yêu cầu đối chiếu khuôn mặt.

---

## 6. Minh chứng demo
* **Container running:** Chạy lệnh `docker compose ps` để kiểm tra container `ai-vision` đang ở trạng thái *Up (healthy)*.
* **Health endpoint:** `GET http://localhost:8004/health` trả về trạng thái ok.
* **Demo cấu trúc lỗi chuẩn RFC 7807 (Tiêu chí E):**
  * Gọi API `/detect` bằng Postman/cURL nhưng không đính kèm Bearer token trong Header $\rightarrow$ Phản hồi HTTP 401 Unauthorized kèm payload chi tiết lỗi theo chuẩn **Problem Details**.
  * Gọi API `/detect` có token nhưng payload rỗng (không truyền ảnh) $\rightarrow$ Phản hồi HTTP 400 Bad Request dạng Problem Details:
    ```json
    {
      "type": "https://smart-campus.local/problems/invalid-image",
      "title": "Invalid image",
      "status": 400,
      "detail": "image_url or image_base64 is required",
      "instance": "/detect"
    }
    ```
