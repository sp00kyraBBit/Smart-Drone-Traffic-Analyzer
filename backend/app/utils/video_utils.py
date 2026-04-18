from typing import Tuple


def get_video_metadata(cap) -> dict:
    fps = float(cap.get(5))  # cv2.CAP_PROP_FPS
    total_frames = int(cap.get(7))  # cv2.CAP_PROP_FRAME_COUNT
    width = int(cap.get(3))  # cv2.CAP_PROP_FRAME_WIDTH
    height = int(cap.get(4))  # cv2.CAP_PROP_FRAME_HEIGHT
    return {
        "fps": fps if fps > 0 else 30.0,
        "total_frames": total_frames,
        "width": width,
        "height": height,
    }


def frame_to_timestamp(frame_index: int, fps: float) -> float:
    if fps <= 0:
        return 0.0
    return round(frame_index / fps, 3)


def compute_centroid(x1: int, y1: int, x2: int, y2: int) -> Tuple[int, int]:
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def bbox_area(x1: int, y1: int, x2: int, y2: int) -> int:
    return max(0, x2 - x1) * max(0, y2 - y1)


def point_in_roi(point: Tuple[int, int], roi: Tuple[int, int, int, int]) -> bool:
    x, y = point
    x1, y1, x2, y2 = roi
    return x1 <= x <= x2 and y1 <= y <= y2

import subprocess
from pathlib import Path


def convert_to_browser_mp4(input_path: str, output_path: str) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vcodec", "libx264",
        "-acodec", "aac",
        "-movflags", "+faststart",
        output_path,
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)