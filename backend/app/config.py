from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
REPORT_DIR = BASE_DIR / "reports"
JOB_DIR = BASE_DIR / "jobs"

ALLOWED_EXTENSIONS = {".mp4"}

YOLO_MODEL_NAME = "yolov8n.pt"
CONFIDENCE_THRESHOLD = 0.35
MIN_BOX_AREA = 800
FRAME_SKIP = 1

ALLOWED_CLASSES = {"car", "bus", "truck", "motorcycle"}

MIN_STABLE_FRAMES = 4
MIN_ROI_FRAMES = 2

REID_IOU_THRESHOLD = 0.35
REID_MAX_LOST_FRAMES = 45

USE_ROI = True
ROI = (40, 5, 1220, 700)

# For visualization only — stored as flat tuple (x1, y1, x2, y2)
COUNTING_LINE_COORDS = (300, 350, 1100, 350)