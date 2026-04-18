from typing import Dict, List, Tuple


class CounterService:
    def __init__(
        self,
        min_stable_frames: int = 4,
        min_roi_frames: int = 2,
        counting_line_y: int = 350,
    ):
        self.counting_line_y = counting_line_y
        self.min_stable_frames = min_stable_frames
        self.min_roi_frames = min_roi_frames

        self.track_history: Dict[int, dict] = {}
        self.counted_ids: set = set()

        self.type_counts: Dict[str, int] = {
            "car": 0,
            "truck": 0,
            "bus": 0,
            "motorcycle": 0,
        }

        self.count_events: List[dict] = []

    def _crossed_horizontal_line(self, prev_centroid, curr_centroid) -> bool:
        if prev_centroid is None or curr_centroid is None:
            return False
        prev_y = prev_centroid[1]
        curr_y = curr_centroid[1]
        line_y = self.counting_line_y
        return (prev_y < line_y <= curr_y) or (prev_y > line_y >= curr_y)

    def _register_count(
        self,
        canonical_id: int,
        class_name: str,
        frame_index: int,
        timestamp_sec: float,
        reason: str,
    ) -> None:
        self.counted_ids.add(canonical_id)

        if class_name in self.type_counts:
            self.type_counts[class_name] += 1
        else:
            self.type_counts[class_name] = 1

        self.count_events.append({
            "canonical_id": canonical_id,
            "vehicle_type": class_name,
            "count_frame": frame_index,
            "count_timestamp_sec": timestamp_sec,
            "count_reason": reason,
        })

    def update(
        self,
        tracked_objects: List[dict],
        frame_index: int,
        timestamp_sec: float,
    ) -> List[dict]:
        for obj in tracked_objects:
            canonical_id = obj.get("canonical_id", obj["track_id"])
            class_name = obj["class_name"]
            curr_centroid = obj["centroid"]
            inside_roi = bool(obj.get("inside_roi", False))

            if canonical_id not in self.track_history:
                self.track_history[canonical_id] = {
                    "frames_seen": 0,
                    "frames_inside_roi": 0,
                    "last_centroid": None,
                    "class_name": class_name,
                    "counted": False,
                    "first_seen_frame": frame_index,
                    "last_seen_frame": frame_index,
                }

            history = self.track_history[canonical_id]
            history["frames_seen"] += 1
            history["last_seen_frame"] = frame_index

            if inside_roi:
                history["frames_inside_roi"] += 1

            crossed = self._crossed_horizontal_line(history["last_centroid"], curr_centroid)
            stable_enough = history["frames_seen"] >= self.min_stable_frames
            roi_enough = history["frames_inside_roi"] >= self.min_roi_frames

            counted_now = False

            if canonical_id not in self.counted_ids:
                if (stable_enough and roi_enough) or crossed:
                    reason = "line_cross" if crossed else "stable_roi"
                    self._register_count(
                        canonical_id, class_name, frame_index, timestamp_sec, reason
                    )
                    history["counted"] = True
                    counted_now = True

            history["last_centroid"] = curr_centroid

            obj["counted"] = canonical_id in self.counted_ids
            obj["counted_now"] = counted_now
            obj["crossed_line"] = crossed

        return tracked_objects

    def get_summary(self, processing_duration_sec: float) -> dict:
        total_unique = sum(self.type_counts.values())
        return {
            "total_unique_vehicles": total_unique,
            "car": self.type_counts.get("car", 0),
            "truck": self.type_counts.get("truck", 0),
            "bus": self.type_counts.get("bus", 0),
            "motorcycle": self.type_counts.get("motorcycle", 0),
            "processing_duration_sec": round(processing_duration_sec, 3),
        }

    def get_count_events(self) -> List[dict]:
        return self.count_events