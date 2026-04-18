import time
import cv2

from app.config import (
    COUNTING_LINE_COORDS,
    MIN_STABLE_FRAMES,
    MIN_ROI_FRAMES,
    FRAME_SKIP,
    USE_ROI,
    ROI,
)
from app.services.detector_tracker import DetectorTracker
from app.services.counter_service import CounterService
from app.services.report_service import export_excel
from app.utils.file_utils import get_output_video_path, get_report_path
from app.utils.video_utils import (
    get_video_metadata,
    frame_to_timestamp,
    point_in_roi,
    convert_to_browser_mp4,
)
from app.utils.draw_utils import (
    draw_box_and_label,
    draw_counting_line,
    draw_summary_overlay,
    draw_roi,
)


def process_video(job_id: str, input_video_path: str, job_updater=None) -> dict:
    start_time = time.time()

    if job_updater:
        job_updater(0, 0, 0, "Opening input video...")

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise RuntimeError("Could not open input video.")

    metadata = get_video_metadata(cap)
    fps = metadata["fps"]
    total_frames = metadata["total_frames"]
    width = metadata["width"]
    height = metadata["height"]

    if job_updater:
        job_updater(1, 0, total_frames, "Video opened. Initializing detector...")

    output_video_path = get_output_video_path(job_id)
    temp_output_video_path = output_video_path.with_name(
        f"{output_video_path.stem}_temp.mp4"
    )
    report_path = get_report_path(job_id)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(temp_output_video_path), fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError("Could not create output video writer.")

    detector_tracker = DetectorTracker()

    # CounterService only gets the Y coordinate integer — nothing that
    # ultralytics could ever misinterpret as a count_line parameter
    line_y = COUNTING_LINE_COORDS[1]  # 350
    counter_service = CounterService(
        min_stable_frames=MIN_STABLE_FRAMES,
        min_roi_frames=MIN_ROI_FRAMES,
        counting_line_y=line_y,
    )

    if job_updater:
        job_updater(2, 0, total_frames, "Model initialized. Processing frames...")

    frame_index = 0
    detection_logs = []
    last_annotated_frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_index += 1
        timestamp_sec = frame_to_timestamp(frame_index, fps)

        if FRAME_SKIP > 1 and frame_index % FRAME_SKIP != 0:
            if last_annotated_frame is not None:
                writer.write(last_annotated_frame)
            else:
                writer.write(frame)
            if job_updater and total_frames > 0:
                progress = max(2, int((frame_index / total_frames) * 100))
                job_updater(progress, frame_index, total_frames, "Skipping frames...")
            continue

        tracked_objects = detector_tracker.process_frame(frame, frame_index)

        prepared_objects = []
        for obj in tracked_objects:
            inside_roi = True
            if USE_ROI:
                inside_roi = point_in_roi(obj["centroid"], ROI)
            obj["inside_roi"] = inside_roi
            prepared_objects.append(obj)

        updated_objects = counter_service.update(prepared_objects, frame_index, timestamp_sec)

        for obj in updated_objects:
            x1, y1, x2, y2 = obj["bbox"]

            detection_logs.append({
                "frame_index": frame_index,
                "timestamp_sec": timestamp_sec,
                "track_id": obj.get("canonical_id", obj["track_id"]),
                "raw_track_id": obj["track_id"],
                "reidentified": obj.get("reidentified", False),
                "vehicle_type": obj["class_name"],
                "confidence": obj["confidence"],
                "bbox_x1": x1,
                "bbox_y1": y1,
                "bbox_x2": x2,
                "bbox_y2": y2,
                "inside_roi": obj.get("inside_roi", False),
                "counted_flag": obj.get("counted", False),
                "counted_now_flag": obj.get("counted_now", False),
                "crossed_line": obj.get("crossed_line", False),
            })

            display_id = obj.get("canonical_id", obj["track_id"])
            label = f"ID {display_id} | {obj['class_name']}"
            if obj.get("inside_roi"):
                label += " | ROI"
            if obj.get("reidentified"):
                label += " | REID"

            draw_box_and_label(frame, obj["bbox"], label, counted=obj.get("counted", False))

        # draw_counting_line expects ((x1,y1),(x2,y2)) format — only used for visuals
        line_pts = (
            (COUNTING_LINE_COORDS[0], COUNTING_LINE_COORDS[1]),
            (COUNTING_LINE_COORDS[2], COUNTING_LINE_COORDS[3]),
        )
        draw_counting_line(frame, line_pts)

        if USE_ROI:
            draw_roi(frame, ROI)

        live_summary = {
            "Total": sum(counter_service.type_counts.values()),
            "Car": counter_service.type_counts.get("car", 0),
            "Truck": counter_service.type_counts.get("truck", 0),
            "Bus": counter_service.type_counts.get("bus", 0),
            "Motorcycle": counter_service.type_counts.get("motorcycle", 0),
        }
        draw_summary_overlay(frame, live_summary)

        writer.write(frame)
        last_annotated_frame = frame.copy()

        if job_updater and total_frames > 0:
            progress = max(2, min(98, int((frame_index / total_frames) * 100)))
            job_updater(progress, frame_index, total_frames, "Detecting and counting vehicles...")

    cap.release()
    writer.release()

    if job_updater:
        job_updater(99, frame_index, total_frames, "Re-encoding for browser playback...")

    convert_to_browser_mp4(str(temp_output_video_path), str(output_video_path))

    if temp_output_video_path.exists():
        temp_output_video_path.unlink()

    if job_updater:
        job_updater(99, frame_index, total_frames, "Generating Excel report...")

    processing_duration_sec = time.time() - start_time
    summary = counter_service.get_summary(processing_duration_sec)
    count_events = counter_service.get_count_events()

    export_excel(report_path, summary, count_events, detection_logs)

    if job_updater:
        job_updater(100, frame_index, total_frames, "Completed.")

    return {
        "output_video_path": str(output_video_path),
        "report_path": str(report_path),
        "summary": summary,
    }