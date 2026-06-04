# ============================================================
# notification.py - Lưu ảnh, bật còi IoT, gửi Zalo tùy chọn
# ============================================================

import os
import time
import threading

import cv2
import config

try:
    import requests
except Exception:
    requests = None

try:
    import pyautogui
    import pyperclip
except Exception:
    pyautogui = None
    pyperclip = None


class AlertManager:
    def __init__(self):
        self.last_alert = 0
        self.alert_count = 0
        self.lock = threading.Lock()

    def get_cooldown_remaining(self):
        elapsed = time.time() - self.last_alert
        return max(0, config.ALERT_COOLDOWN - elapsed)

    def trigger_alert(self, frame):
        with self.lock:
            if time.time() - self.last_alert < config.ALERT_COOLDOWN:
                return False

            self.last_alert = time.time()
            self.alert_count += 1

        threading.Thread(
            target=self._handle_alert,
            args=(frame.copy(),),
            daemon=True
        ).start()

        return True

    def _handle_alert(self, frame):
        os.makedirs(config.SAVE_FOLDER, exist_ok=True)

        filename = f"intrusion_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(config.SAVE_FOLDER, filename)

        cv2.imwrite(path, frame)

        print(f"🚨 PHÁT HIỆN XÂM NHẬP - đã lưu ảnh: {path}")

        # ===== CÒI IOT ESP8266 / ESP32 =====
        if getattr(config, "ENABLE_IOT_ALARM", False):
            self._trigger_iot_alarm()

        # ===== GỬI ZALO =====
        if config.ENABLE_ZALO:
            self._send_zalo()

    def _trigger_iot_alarm(self):
        if requests is None:
            print("[WARN] Chưa cài thư viện requests nên không gọi được còi IoT.")
            print("[GỢI Ý] Chạy: pip install requests")
            return

        try:
            print("[INFO] Đang gửi lệnh bật còi IoT...")

            response = requests.get(
                config.IOT_ALARM_URL,
                params={
                    "duration": config.IOT_ALARM_SECONDS
                },
                timeout=3
            )

            if response.status_code == 200:
                print("[INFO] Đã bật còi IoT thành công.")
            else:
                print(f"[WARN] IoT trả về mã lỗi: {response.status_code}")

        except Exception as e:
            print(f"[ERROR] Không gửi được lệnh còi IoT: {e}")

    def _send_zalo(self):
        if pyautogui is None or pyperclip is None:
            print("[WARN] Chưa cài pyautogui/pyperclip nên không gửi Zalo.")
            print("[GỢI Ý] Chạy: pip install pyautogui pyperclip")
            return

        try:
            print("[INFO] Chuẩn bị gửi Zalo...")
            print(f"[INFO] Click vào tọa độ ({config.ZALO_CLICK_X}, {config.ZALO_CLICK_Y})")

            time.sleep(1.5)

            pyautogui.click(config.ZALO_CLICK_X, config.ZALO_CLICK_Y)
            time.sleep(0.8)

            pyautogui.click(config.ZALO_CLICK_X, config.ZALO_CLICK_Y)
            time.sleep(0.3)

            pyperclip.copy(config.ZALO_MESSAGE)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.3)

            pyautogui.press("enter")

            print(f"[INFO] Đã gửi Zalo: {config.ZALO_MESSAGE}")

        except Exception as e:
            print(f"[ERROR] Không gửi được Zalo: {e}")