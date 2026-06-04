# Phát hiện xâm nhập trái phép bằng YOLOv5 chạy trên Web

## 1. Mục tiêu đề tài
Hệ thống sử dụng YOLOv5 để phát hiện người trong video/camera. Người dùng có thể tự kẻ một vùng cấm trên giao diện web. Khi có người đi vào vùng cấm, hệ thống sẽ cảnh báo, lưu ảnh xâm nhập và hiển thị trạng thái trên web.

## 2. Chức năng chính
- Phát hiện người bằng YOLOv5.
- Chạy bằng video có sẵn hoặc camera.
- Xem trực tiếp trên web bằng Flask.
- Kẻ vùng cấm trực tiếp trên web.
- Cảnh báo khi người đi vào vùng cấm.
- Lưu ảnh xâm nhập vào thư mục `intrusion_images`.
- Có cooldown để tránh cảnh báo liên tục.
- Có thể bật/tắt gửi Zalo trong `config.py`.

## 3. Cấu trúc thư mục
```text
yolov5_intrusion_web/
├── app.py
├── config.py
├── detection.py
├── notification.py
├── requirements.txt
├── README.md
├── yolov5s.pt
├── demo.mp4
├── templates/
│   └── index.html
└── intrusion_images/
```

## 4. Cài đặt
```bash
pip install -r requirements.txt
```

Nếu chưa có PyTorch:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

## 5. Chuẩn bị video demo
Đổi tên video thành `demo.mp4` và đặt cùng thư mục với `app.py`.

Hoặc sửa trong `config.py`:
```python
VIDEO_PATH = "ten_video_cua_ban.mp4"
```

## 6. Chạy chương trình
```bash
python app.py
```

Mở trình duyệt:
```text
http://localhost:5000
```

## 7. Cách demo
1. Chạy `python app.py`.
2. Mở web `http://localhost:5000`.
3. Click nhiều điểm trên video để vẽ vùng cấm.
4. Nhấn **Lưu vùng cấm**.
5. Khi người đi vào vùng cấm, hệ thống hiển thị cảnh báo đỏ, tăng số lượng cảnh báo và lưu ảnh vào `intrusion_images`.

## 8. Cấu hình quan trọng
Trong `config.py`:
```python
SOURCE_TYPE = "video"      # hoặc "camera"
VIDEO_PATH = "demo.mp4"
DEMO_ALWAYS_GUARD = True    # luôn cảnh báo khi demo
ENABLE_ZALO = False         # bật True nếu muốn gửi Zalo thật
ALERT_COOLDOWN = 10
```

## 9. Nguyên lý hoạt động
1. Flask mở luồng video/camera.
2. YOLOv5 nhận diện đối tượng `person`.
3. Hệ thống lấy điểm chân của người từ bounding box.
4. Nếu điểm chân nằm trong vùng cấm, người đó được xem là xâm nhập.
5. Hệ thống kích hoạt cảnh báo và lưu ảnh.

## 10. Lưu ý
- Nếu muốn demo dễ, nên để `DEMO_ALWAYS_GUARD = True`.
- Nếu dùng camera, đổi `SOURCE_TYPE = "camera"`.
- Nếu không muốn gửi Zalo khi demo, để `ENABLE_ZALO = False`.
