# PLAN: Tích hợp Kit IoT ESP8266 + Còi Báo Động vào Hệ thống YOLOv5

## 📋 Overview

**Mục tiêu**: Kết nối kit IoT **ESP8266 (NodeMCU)** + **Active Buzzer** vào hệ thống phát hiện xâm nhập đang chạy Flask. Khi YOLOv5 phát hiện người xâm nhập vùng cấm, Flask sẽ gửi HTTP GET request tới ESP8266, và ESP8266 sẽ kích hoạt còi báo động vật lý trong một khoảng thời gian nhất định.

**Project Type**: BACKEND + IoT Firmware

**Trạng thái hiện tại**:
- ✅ Phía Python/Flask đã có sẵn `ENABLE_IOT_ALARM = True` và `IOT_ALARM_URL = "http://192.168.100.105/alarm"` trong `config.py`
- ✅ `notification.py` đã có hàm `_trigger_iot_alarm()` gửi request: `GET /alarm?duration=3`
- ❌ Chưa có code cho ESP8266
- ❌ ESP8266 chưa kết nối Wi-Fi vào cùng mạng nội bộ

---

## 🎯 Success Criteria (Tiêu chí thành công)

| # | Tiêu chí | Kiểm tra bằng cách |
|---|----------|-------------------|
| 1 | ESP8266 kết nối Wi-Fi thành công | Serial Monitor hiển thị IP `192.168.100.105` |
| 2 | ESP8266 lắng nghe HTTP tại `/alarm` | Truy cập `http://192.168.100.105/alarm?duration=3` từ trình duyệt thấy còi kêu |
| 3 | Active Buzzer kêu đúng thời gian `duration` giây | Đo bằng đồng hồ |
| 4 | Flask gọi được IoT khi phát hiện xâm nhập | Chạy toàn bộ hệ thống, có người vào vùng cấm → còi kêu |
| 5 | Không bị block luồng chính Flask | Serial Monitor không thấy lỗi timeout gây crash Flask |

---

## 🔧 Tech Stack

| Thành phần | Công nghệ | Lý do |
|------------|-----------|-------|
| **Firmware ESP8266** | Arduino IDE + `ESP8266WiFi.h` + `ESP8266WebServer.h` | Thư viện phổ biến nhất, dễ cấu hình HTTP server |
| **Giao tiếp** | HTTP GET qua Wi-Fi LAN | Đơn giản, Flask đã hỗ trợ sẵn qua `requests.get()` |
| **Buzzer** | Active Buzzer nối vào chân D5 (GPIO14) | Active buzzer chỉ cần digitalWrite HIGH/LOW |
| **IP tĩnh** | Cấu hình IP tĩnh `192.168.100.105` trong firmware | Flask đã hardcode IP này trong `config.py` |
| **Python** | `notification.py` (đã có), chỉ cần verify | Flask gọi `requests.get(IOT_ALARM_URL, params={"duration": IOT_ALARM_SECONDS})` |

---

## 📁 File Structure (Các file cần tạo/sửa)

```text
yolov5_intrusion_web/
├── config.py                          ← [SỬA] Dọn duplicate, xác nhận IP, bật ENABLE_IOT_ALARM
├── notification.py                    ← [KIỂM TRA] Hàm _trigger_iot_alarm() đã đúng chưa
└── docs/
    ├── PLAN-iot-alarm-esp8266.md      ← File này
    └── esp8266_alarm/
        └── esp8266_alarm.ino          ← [TẠO MỚI] Firmware Arduino cho ESP8266
```

---

## 📊 Task Breakdown

### TASK 1 — Viết Firmware Arduino cho ESP8266
**Agent**: `backend-specialist` (IoT Firmware)
**Priority**: P0 (Nhiệm vụ cốt lõi)
**Phụ thuộc**: Không

**INPUT**:
- Kit: ESP8266 NodeMCU
- Buzzer: Active Buzzer nối chân D5 (GPIO14)
- Yêu cầu API: `GET /alarm?duration=3` → còi kêu 3 giây

**OUTPUT**: File `docs/esp8266_alarm/esp8266_alarm.ino` hoàn chỉnh, gồm:
- Kết nối Wi-Fi với SSID & Password được cấu hình
- Thiết lập IP tĩnh `192.168.100.105` (gateway, subnet phù hợp mạng của bạn)
- HTTP Web Server lắng nghe trên port 80
- Route `/alarm`: đọc param `duration`, bật buzzer HIGH → delay → tắt buzzer LOW
- Route `/`: response "ESP8266 Alarm Ready" (health check)
- Non-blocking buzzer dùng `millis()` để ESP8266 vẫn xử lý request khi còi đang kêu
- Serial debug log: IP, trạng thái kết nối, khi nhận request

**VERIFY**:
- [ ] Upload lên ESP8266 thành công (không lỗi compile)
- [ ] Serial Monitor hiển thị `Connected! IP: 192.168.100.105`
- [ ] Gõ `http://192.168.100.105/alarm?duration=3` trên trình duyệt → còi kêu 3 giây
- [ ] Gõ `http://192.168.100.105/` → hiện text "ESP8266 Alarm Ready"

---

### TASK 2 — Dọn dẹp và Xác nhận config.py + notification.py
**Agent**: `backend-specialist`
**Priority**: P1
**Phụ thuộc**: TASK 1

**INPUT**:
- `config.py` hiện tại (có duplicate dòng `ENABLE_ZALO`, `DEMO_ALWAYS_GUARD`, `ALERT_COOLDOWN`)
- `notification.py` hàm `_trigger_iot_alarm()`

**OUTPUT**: `config.py` được dọn dẹp sạch, không còn duplicate:
```python
# config.py - Các dòng phải đúng
ENABLE_IOT_ALARM = True
IOT_ALARM_URL    = "http://192.168.100.105/alarm"
IOT_ALARM_SECONDS = 3
ALERT_COOLDOWN   = 10   # Chỉ xuất hiện 1 lần
DEMO_ALWAYS_GUARD = True # Chỉ xuất hiện 1 lần
ENABLE_ZALO      = False # Tắt Zalo khi demo để tránh gửi thật
```

**VERIFY**:
- [ ] `python -c "import config; print(config.ENABLE_IOT_ALARM, config.IOT_ALARM_URL, config.IOT_ALARM_SECONDS)"`
  → Output: `True http://192.168.100.105/alarm 3`
- [ ] Không có duplicate config gây nhầm lẫn

---

### TASK 3 — Test End-to-End toàn luồng
**Agent**: `test-engineer`
**Priority**: P2
**Phụ thuộc**: TASK 1 + TASK 2

**INPUT**:
- ESP8266 đã cắm điện, kết nối cùng mạng Wi-Fi với máy tính
- Hệ thống Flask đang chạy `python app.py`
- Video demo `video.mp4`

**Các bước kiểm tra tuần tự**:

**Bước 1 - Test ESP8266 độc lập**:
```
Mở trình duyệt → http://192.168.100.105/alarm?duration=3
Kết quả mong đợi: Còi kêu 3 giây, trả về JSON {"status": "ok"}
```

**Bước 2 - Test từ Python**:
```python
import requests
r = requests.get("http://192.168.100.105/alarm", params={"duration": 2}, timeout=5)
print(r.status_code, r.text)
# Mong đợi: 200 {"status": "ok", "duration": 2}
```

**Bước 3 - Test toàn hệ thống**:
```
1. python app.py
2. Mở http://localhost:5000
3. Vẽ vùng cấm → Lưu vùng cấm → Bắt đầu
4. Có người đi vào vùng cấm trong video
5. Quan sát: Serial Monitor ESP8266 + Flask console + Còi kêu
```

**VERIFY**:
- [ ] Serial Monitor ESP8266 hiển thị `[ALARM] Received duration=3`
- [ ] Flask console hiển thị `[INFO] Đã bật còi IoT thành công.`
- [ ] Còi kêu vật lý khi có xâm nhập
- [ ] Không có `ConnectionError`, `Timeout`, hay `Exception` trong Flask log
- [ ] Cooldown hoạt động: Còi không kêu liên tục, chờ đủ `ALERT_COOLDOWN` giây

---

## 🔌 Sơ đồ kết nối phần cứng

```
ESP8266 NodeMCU          Active Buzzer
─────────────────        ─────────────
D5 (GPIO14)  ──────────► (+) Chân dương (chân có dấu +)
GND          ──────────► (-) Chân âm   (chân còn lại)

Lưu ý Active Buzzer:
  - digitalWrite(BUZZER_PIN, HIGH) → BẬT còi kêu
  - digitalWrite(BUZZER_PIN, LOW)  → TẮT còi
  - Không cần điện trở (buzzer 3.3V/5V đều hoạt động với D5 của NodeMCU)
```

---

## 🌐 Luồng dữ liệu (Data Flow)

```
Video/Camera
     │
     ▼
YOLOv5 phát hiện Person
     │
     ▼
persons_in_roi() → CÓ người trong vùng cấm
     │
     ▼
alert_manager.trigger_alert(frame)  [có cooldown]
     │
     ▼
notification._handle_alert() [chạy trong Thread riêng]
     ├──► cv2.imwrite() → lưu ảnh intrusion_images/
     ├──► _trigger_iot_alarm()
     │         │
     │         ▼
     │    requests.GET http://192.168.100.105/alarm?duration=3
     │         │
     │         ▼
     │    ESP8266 nhận HTTP request
     │         │
     │         ▼
     │    digitalWrite(D5, HIGH)  → Còi kêu
     │    millis() non-blocking 3000ms
     │    digitalWrite(D5, LOW)   → Tắt còi
     │
     └──► _send_zalo() [tùy chọn, hiện đang tắt]
```

---

## ⚠️ Lưu ý quan trọng

> **IP tĩnh**: ESP8266 phải dùng IP tĩnh `192.168.100.105`. Cần xác nhận gateway và subnet của mạng Wi-Fi bạn đang dùng (thường là `192.168.100.1` và `255.255.255.0`).

> **Cùng mạng LAN**: Máy tính chạy Flask và ESP8266 phải kết nối **cùng một Wi-Fi** (cùng subnet). Nếu dùng hotspot điện thoại, cả 2 đều phải vào hotspot đó.

> **Non-blocking buzzer**: Dùng `millis()` thay vì `delay()` để ESP8266 vẫn nhận request mới trong khi còi đang kêu (tránh bỏ lỡ cảnh báo).

> **Timeout Flask**: Hàm `_trigger_iot_alarm()` đã có `timeout=3` và chạy trong `daemon Thread` riêng, đảm bảo Flask không bị block nếu ESP8266 offline.

---

## Phase X: Verification Checklist

- [ ] ESP8266 Serial Monitor: `Connected! IP: 192.168.100.105`
- [ ] Trình duyệt `http://192.168.100.105/` → "ESP8266 Alarm Ready"
- [ ] Trình duyệt `http://192.168.100.105/alarm?duration=2` → còi kêu đúng 2 giây
- [ ] Python test script gọi HTTP → còi kêu, status 200
- [ ] Chạy Flask toàn hệ thống → phát hiện xâm nhập → còi kêu
- [ ] Flask log: `[INFO] Đã bật còi IoT thành công.`
- [ ] Không có exception/crash trong Flask log
- [ ] `ALERT_COOLDOWN` hoạt động, không spam còi
