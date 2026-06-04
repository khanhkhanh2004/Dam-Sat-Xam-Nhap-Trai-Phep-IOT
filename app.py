# ============================================================
# app.py - Web app phát hiện xâm nhập trái phép bằng YOLOv5
# Chạy: python app.py
# ============================================================

import time
import threading
from datetime import datetime
from typing import List, Tuple

import cv2
from flask import Flask, Response, jsonify, render_template, request

import config
from detection import PersonDetector, is_guard_time, persons_in_roi
from notification import AlertManager


app = Flask(__name__)

frame_lock = threading.Lock()

current_frame = None
system_running = False
source_active = False
intrusion_active = False

persons_count = 0
intruders_count = 0
last_alert_time = None

roi_points: List[Tuple[int, int]] = list(getattr(config, "DEFAULT_ROI", []))

alert_manager = AlertManager()
detector = None


def open_source():
    if config.SOURCE_TYPE.lower() == "camera":
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        return cap

    return cv2.VideoCapture(config.VIDEO_PATH)


def draw_roi(frame, roi):
    if len(roi) < 3:
        cv2.putText(
            frame,
            "Vui long thiet lap vung cam truoc khi bat dau",
            (10, 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (0, 255, 255),
            2
        )
        return frame

    import numpy as np

    pts = np.array(roi, dtype=np.int32)
    overlay = frame.copy()

    cv2.fillPoly(overlay, [pts], (0, 255, 255))
    cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)
    cv2.polylines(frame, [pts], True, (0, 255, 255), 3)

    cv2.putText(
        frame,
        "VUNG CAM",
        tuple(pts[0]),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    return frame


def draw_overlay(frame, is_intrusion, count, intruders):
    h, w = frame.shape[:2]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cv2.rectangle(frame, (0, 0), (w, 42), (10, 10, 10), -1)
    cv2.putText(
        frame,
        f"HE THONG PHAT HIEN XAM NHAP YOLOv5 | {now}",
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (230, 230, 230),
        2
    )

    guard = is_guard_time()

    if guard:
        mode_text = "CHE DO: GIAM SAT / DEMO"
        mode_color = (0, 180, 255)
    else:
        mode_text = "CHE DO: TRONG GIO HOC"
        mode_color = (0, 255, 0)

    cv2.rectangle(frame, (0, h - 68), (w, h), (10, 10, 10), -1)

    cv2.putText(
        frame,
        mode_text,
        (10, h - 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        mode_color,
        2
    )

    cv2.putText(
        frame,
        f"So nguoi: {count} | Trong vung cam: {intruders} | Canh bao: {alert_manager.alert_count}",
        (10, h - 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (190, 190, 190),
        1
    )

    if is_intrusion:
        cv2.rectangle(frame, (0, 46), (w, 102), (0, 0, 190), -1)

        if int(time.time()) % 2 == 0:
            text = "!!! CANH BAO XAM NHAP TRAI PHEP !!!"
            size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 0.9, 2)

            cv2.putText(
                frame,
                text,
                ((w - size[0]) // 2, 83),
                cv2.FONT_HERSHEY_DUPLEX,
                0.9,
                (255, 255, 255),
                2
            )

    return frame


def processing_loop():
    global current_frame, system_running, source_active, intrusion_active
    global persons_count, intruders_count, last_alert_time, detector

    with frame_lock:
        if len(roi_points) < 3:
            print("[ERROR] Chưa thiết lập vùng cấm.")
            system_running = False
            source_active = False
            return

    detector = PersonDetector()
    cap = open_source()

    if not cap.isOpened():
        print("[ERROR] Không mở được nguồn video/camera. Kiểm tra VIDEO_PATH hoặc CAMERA_INDEX.")
        source_active = False
        system_running = False
        return

    source_active = True
    system_running = True

    print("[INFO] Hệ thống đang chạy...")

    while system_running:
        ret, frame = cap.read()

        if not ret:
            if config.SOURCE_TYPE.lower() == "video" and config.LOOP_VIDEO:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            time.sleep(0.1)
            continue

        frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
        annotated, persons, _ = detector.detect(frame)

        with frame_lock:
            roi_copy = list(roi_points)

        intruders = persons_in_roi(persons, roi_copy)

        persons_count = len(persons)
        intruders_count = len(intruders)
        intrusion_active = is_guard_time() and intruders_count > 0

        display = draw_roi(annotated, roi_copy)
        display = draw_overlay(display, intrusion_active, persons_count, intruders_count)

        if intrusion_active:
         if alert_manager.trigger_alert(display):
          print("🚨 PHÁT HIỆN XÂM NHẬP - đã kích hoạt cảnh báo")
        last_alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with frame_lock:
            current_frame = display.copy()

        time.sleep(0.03)

    cap.release()
    source_active = False
    intrusion_active = False
    print("[INFO] Đã dừng hệ thống.")


def generate_frames():
    while True:
        with frame_lock:
            frame = None if current_frame is None else current_frame.copy()

        if frame is None:
            import numpy as np

            frame = 255 * np.ones(
                (config.FRAME_HEIGHT, config.FRAME_WIDTH, 3),
                dtype="uint8"
            )

            cv2.putText(
                frame,
                "Vui long chon vung cam roi bam BAT DAU",
                (35, config.FRAME_HEIGHT // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 0, 0),
                2
            )

        success, buffer = cv2.imencode(".jpg", frame)

        if success:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                buffer.tobytes() +
                b"\r\n"
            )

        time.sleep(0.03)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/api/status")
def status():
    return jsonify({
        "source_active": source_active,
        "running": system_running,
        "guard_mode": is_guard_time(),
        "intrusion": intrusion_active,
        "persons": persons_count,
        "intruders": intruders_count,
        "alerts": alert_manager.alert_count,
        "cooldown": round(alert_manager.get_cooldown_remaining(), 1),
        "last_alert": last_alert_time,
        "roi": roi_points,
        "roi_locked": system_running,
        "source_type": config.SOURCE_TYPE,
    })


@app.route("/api/roi", methods=["POST"])
def set_roi():
    global roi_points

    with frame_lock:
        if system_running:
            return jsonify({
                "ok": False,
                "message": "Hệ thống đang chạy, không thể thay đổi vùng cấm."
            }), 400

    data = request.get_json(force=True)
    points = data.get("points", [])

    if len(points) < 3:
        return jsonify({
            "ok": False,
            "message": "Vùng cấm cần ít nhất 3 điểm."
        }), 400

    clean = []

    for p in points:
        x = int(max(0, min(config.FRAME_WIDTH - 1, p["x"])))
        y = int(max(0, min(config.FRAME_HEIGHT - 1, p["y"])))
        clean.append((x, y))

    with frame_lock:
        roi_points = clean

    return jsonify({
        "ok": True,
        "message": "Đã lưu vùng cấm.",
        "roi": roi_points
    })


@app.route("/api/roi/clear", methods=["POST"])
def clear_roi():
    global roi_points, current_frame, persons_count, intruders_count, intrusion_active

    with frame_lock:
        if system_running:
            return jsonify({
                "ok": False,
                "message": "Hệ thống đang chạy, không thể xóa vùng cấm."
            }), 400

        roi_points = []
        current_frame = None
        persons_count = 0
        intruders_count = 0
        intrusion_active = False

    return jsonify({
        "ok": True,
        "message": "Đã xóa vùng cấm.",
        "roi": []
    })


@app.route("/api/start", methods=["POST"])
def start():
    global system_running

    with frame_lock:
        if len(roi_points) < 3:
            return jsonify({
                "ok": False,
                "message": "Bạn cần chọn và lưu vùng cấm trước khi bắt đầu."
            }), 400

    if not system_running:
        threading.Thread(target=processing_loop, daemon=True).start()

    return jsonify({
        "ok": True,
        "message": "Hệ thống đã bắt đầu giám sát."
    })


@app.route("/api/stop", methods=["POST"])
def stop():
    global system_running

    system_running = False

    return jsonify({
        "ok": True,
        "message": "Hệ thống đã dừng. Bạn có thể chỉnh sửa vùng cấm."
    })


if __name__ == "__main__":
    print("=" * 60)
    print(" HỆ THỐNG PHÁT HIỆN XÂM NHẬP TRÁI PHÉP BẰNG YOLOv5")
    print("=" * 60)
    print(f" Web        : http://localhost:{config.FLASK_PORT}")
    print(f" Nguồn      : {config.SOURCE_TYPE}")
    print(f" Video      : {config.VIDEO_PATH}")
    print(f" Model      : {config.MODEL_PATH}")
    print(f" Gửi Zalo   : {config.ENABLE_ZALO}")
    print("=" * 60)

    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
        threaded=True,
        use_reloader=False
    )