# ============================================================
# detection.py - Nhận diện người bằng YOLOv5 + kiểm tra ROI
# ============================================================

import os
from datetime import datetime
from typing import List, Tuple, Dict

import cv2
import torch

import config

Point = Tuple[int, int]
BBox = Tuple[int, int, int, int]


class PersonDetector:
    def __init__(self):
        print("[INFO] Đang tải YOLOv5...")

        if os.path.exists(config.MODEL_PATH):
            self.model = torch.hub.load(
                "ultralytics/yolov5",
                "custom",
                path=config.MODEL_PATH,
                force_reload=False
            )
        else:
            self.model = torch.hub.load(
                "ultralytics/yolov5",
                config.YOLO_MODEL,
                pretrained=True,
                force_reload=False
            )

        self.model.conf = config.CONFIDENCE_THRESHOLD
        self.model.classes = [config.PERSON_CLASS_ID]
        print("[INFO] YOLOv5 đã sẵn sàng.")

    def detect(self, frame):
        """Trả về frame đã vẽ bbox, danh sách người, có người hay không."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.model(rgb, size=640)
        detections = results.pandas().xyxy[0]

        persons: List[Dict] = []
        annotated = frame.copy()

        for _, row in detections.iterrows():
            x1 = int(row["xmin"])
            y1 = int(row["ymin"])
            x2 = int(row["xmax"])
            y2 = int(row["ymax"])
            conf = float(row["confidence"])

            box_width = x2 - x1
            box_height = y2 - y1
            aspect_ratio = box_height / max(box_width, 1)

            # Lọc nhận nhầm ghế/đồ vật/box quá nhỏ
            if box_height < config.MIN_BOX_HEIGHT:
                continue
            if box_width < config.MIN_BOX_WIDTH:
                continue
            if aspect_ratio < config.MIN_ASPECT_RATIO:
                continue
            if aspect_ratio > config.MAX_ASPECT_RATIO:
                continue

            person = {
                "bbox": (x1, y1, x2, y2),
                "confidence": conf,
                "foot": ((x1 + x2) // 2, y2),
                "center": ((x1 + x2) // 2, (y1 + y2) // 2),
            }
            persons.append(person)

            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
            label = f"Person {conf:.2f}"
            cv2.rectangle(annotated, (x1, y1 - 25), (x1 + 135, y1), (0, 0, 255), -1)
            cv2.putText(annotated, label, (x1 + 5, y1 - 7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        return annotated, persons, len(persons) > 0


def is_guard_time() -> bool:
    """True nếu hệ thống đang ở chế độ canh gác."""
    if getattr(config, "DEMO_ALWAYS_GUARD", False):
        return True

    now = datetime.now()
    hour = now.hour
    for start, end in config.CLASS_HOURS:
        if start <= hour < end:
            return False
    return True


def point_in_polygon(point: Point, polygon: List[Point]) -> bool:
    if len(polygon) < 3:
        return True

    import numpy as np

    pts = np.array(polygon, dtype=np.int32)
    return cv2.pointPolygonTest(pts, point, False) >= 0


def bbox_touch_polygon(bbox: BBox, polygon: List[Point]) -> bool:
    if len(polygon) < 3:
        return True

    x1, y1, x2, y2 = bbox

    test_points = [
        ((x1 + x2) // 2, (y1 + y2) // 2),
        ((x1 + x2) // 2, y2),
        (x1, y1),
        (x2, y1),
        (x1, y2),
        (x2, y2),
    ]

    for p in test_points:
        if point_in_polygon(p, polygon):
            return True

    for px, py in polygon:
        if x1 <= px <= x2 and y1 <= py <= y2:
            return True

    return False


def persons_in_roi(persons: List[Dict], roi: List[Point]) -> List[Dict]:
    mode = getattr(config, "ROI_HIT_MODE", "bbox")
    intruders = []

    for person in persons:
        if mode == "bbox":
            hit = bbox_touch_polygon(person["bbox"], roi)
        else:
            test_point = person.get(mode, person["foot"])
            hit = point_in_polygon(test_point, roi)

        if hit:
            intruders.append(person)

    return intruders