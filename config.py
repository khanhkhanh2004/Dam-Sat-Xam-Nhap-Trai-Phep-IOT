# ============================================================
# config.py
# ============================================================

SOURCE_TYPE = "video"
VIDEO_PATH = "video.mp4"
LOOP_VIDEO = True
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

MODEL_PATH = "yolov5s.pt"
YOLO_MODEL = "yolov5s"
CONFIDENCE_THRESHOLD = 0.45
PERSON_CLASS_ID = 0

MIN_BOX_HEIGHT = 80
MIN_BOX_WIDTH = 30
MIN_ASPECT_RATIO = 1.0
MAX_ASPECT_RATIO = 4.5

DEFAULT_ROI = []
ROI_HIT_MODE = "bbox"   # sửa từ foot sang bbox để cảnh báo nhanh hơn

DEMO_ALWAYS_GUARD = True
CLASS_HOURS = [
    (10, 11),
    (16, 17),
]

ALERT_COOLDOWN = 5
SAVE_FOLDER = "intrusion_images"
ENABLE_ALARM = True

ENABLE_ZALO = True
ZALO_CLICK_X = 993
ZALO_CLICK_Y = 987
ZALO_MESSAGE = "🚨 CANH BAO: CO NGUOI XAM NHAP TRAI PHEP! 🚨"

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = False

ENABLE_IOT_ALARM = True
IOT_ALARM_URL = "http://192.168.100.105/alarm"
IOT_ALARM_SECONDS = 3