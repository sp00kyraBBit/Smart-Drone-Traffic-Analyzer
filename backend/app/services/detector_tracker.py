from typing import List, Dict

from ultralytics import YOLO

from app.config import (
    YOLO_MODEL_NAME,
    CONFIDENCE_THRESHOLD,
    MIN_BOX_AREA,
    ALLOWED_CLASSES,
    REID_IOU_THRESHOLD,
    REID_MAX_LOST_FRAMES,
)
from app.utils.video_utils import bbox_area, compute_centroid


def compute_iou(box_a, box_b) -> float:
    """Compute Intersection over Union between two bounding boxes [x1,y1,x2,y2]."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    if inter_area == 0:
        return 0.0

    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union_area = area_a + area_b - inter_area

    return inter_area / union_area if union_area > 0 else 0.0


class DetectorTracker:
    """
    Wraps YOLO detection + built-in ByteTrack tracking.

    Re-identification: when YOLO assigns a new track_id to a vehicle that
    was temporarily lost (occlusion, frame boundary), we check IoU against
    recently-lost tracks and remap to the original canonical_id so the
    CounterService never double-counts the same physical vehicle.
    """

    def __init__(self):
        self.model = YOLO(YOLO_MODEL_NAME)

        # Maps raw YOLO track_id -> canonical track_id
        self._id_map: Dict[int, int] = {}

        # Recently lost tracks: canonical_id -> {bbox, class_name, lost_frame}
        self._lost_tracks: Dict[int, dict] = {}

        # Track which canonical ids are currently active
        self._active_canonical_ids: set = set()

    def _canonical_id(self, track_id: int) -> int:
        return self._id_map.get(track_id, track_id)

    def _try_reid(self, track_id: int, class_name: str, bbox, frame_index: int) -> int:
        best_iou = REID_IOU_THRESHOLD
        best_canonical = None

        for canonical_id, info in list(self._lost_tracks.items()):
            if info["class_name"] != class_name:
                continue
            if frame_index - info["lost_frame"] > REID_MAX_LOST_FRAMES:
                del self._lost_tracks[canonical_id]
                continue
            iou = compute_iou(bbox, info["bbox"])
            if iou > best_iou:
                best_iou = iou
                best_canonical = canonical_id

        if best_canonical is not None:
            del self._lost_tracks[best_canonical]
            return best_canonical

        return track_id

    def update_lost_tracks(self, active_raw_ids: set, all_objects: List[dict], frame_index: int):
        currently_active_canonical = {self._canonical_id(tid) for tid in active_raw_ids}

        newly_lost = self._active_canonical_ids - currently_active_canonical
        for canonical_id in newly_lost:
            for obj in all_objects:
                if obj.get("canonical_id") == canonical_id:
                    self._lost_tracks[canonical_id] = {
                        "bbox": obj["bbox"],
                        "class_name": obj["class_name"],
                        "lost_frame": frame_index,
                    }
                    break

        self._active_canonical_ids = currently_active_canonical

    def _should_reject(self, class_name: str, bbox, frame_shape) -> bool:
        x1, y1, x2, y2 = bbox
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)

        frame_h, frame_w = frame_shape[:2]
        frame_area = frame_w * frame_h
        box_area = w * h

        area_ratio = box_area / frame_area
        aspect_ratio = w / h

        if area_ratio > 0.15:
            return True
        if aspect_ratio > 4.5:
            return True

        if class_name in {"bus", "truck"}:
            if area_ratio > 0.10:
                return True
            if aspect_ratio > 3.8:
                return True

        return False

    def process_frame(self, frame, frame_index: int = 0) -> List[Dict]:
        results = self.model.track(
            source=frame,
            persist=True,
            verbose=False,
            conf=CONFIDENCE_THRESHOLD,
            # NOTE: Do NOT pass tracker config with count_line here.
            # Counting is handled entirely by CounterService.
        )

        tracked_objects = []
        if not results:
            return tracked_objects

        result = results[0]
        if result.boxes is None:
            return tracked_objects

        names = result.names
        active_raw_ids = set()

        for box in result.boxes:
            if box.id is None or box.cls is None or box.conf is None:
                continue

            class_id = int(box.cls[0].item())
            class_name = names[class_id]
            confidence = float(box.conf[0].item())

            if class_name not in ALLOWED_CLASSES:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            bbox = [x1, y1, x2, y2]

            area = bbox_area(x1, y1, x2, y2)
            if area < MIN_BOX_AREA:
                continue

            if self._should_reject(class_name, bbox, frame.shape):
                continue

            raw_id = int(box.id[0].item())
            active_raw_ids.add(raw_id)

            if raw_id not in self._id_map:
                canonical = self._try_reid(raw_id, class_name, bbox, frame_index)
                self._id_map[raw_id] = canonical
            else:
                canonical = self._id_map[raw_id]

            centroid = compute_centroid(x1, y1, x2, y2)
            reidentified = (canonical != raw_id)

            tracked_objects.append({
                "track_id": raw_id,
                "canonical_id": canonical,
                "class_name": class_name,
                "confidence": round(confidence, 3),
                "bbox": bbox,
                "centroid": centroid,
                "reidentified": reidentified,
            })

        self.update_lost_tracks(active_raw_ids, tracked_objects, frame_index)

        return tracked_objects