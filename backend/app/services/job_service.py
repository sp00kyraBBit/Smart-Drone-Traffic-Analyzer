import json
import os
from datetime import datetime
from threading import Lock

from app.utils.file_utils import get_job_metadata_path

# In-memory live job state
JOB_STORE = {}
JOB_STORE_LOCK = Lock()


def _now() -> str:
    return datetime.utcnow().isoformat()


def _persist_job_to_disk(job_id: str, job_data: dict) -> None:
    """
    Best-effort backup to disk.
    Status polling should NOT depend on this.
    """
    path = get_job_metadata_path(job_id)
    serialized = json.dumps(job_data, indent=2)

    with path.open("w", encoding="utf-8") as f:
        f.write(serialized)
        f.flush()
        os.fsync(f.fileno())


def create_job(job_id: str, input_video_path: str, original_filename: str) -> dict:
    job = {
        "job_id": job_id,
        "status": "uploaded",
        "progress": 0,
        "current_frame": 0,
        "total_frames": 0,
        "message": "Video uploaded successfully.",
        "input_video_path": input_video_path,
        "original_filename": original_filename,
        "output_video_path": "",
        "report_path": "",
        "summary": {},
        "created_at": _now(),
        "started_at": None,
        "completed_at": None,
        "error": None,
    }

    with JOB_STORE_LOCK:
        JOB_STORE[job_id] = job.copy()

    _persist_job_to_disk(job_id, job)
    return job


def load_job(job_id: str) -> dict:
    """
    Read from memory first.
    Fall back to disk only if needed.
    """
    with JOB_STORE_LOCK:
        if job_id in JOB_STORE:
            return JOB_STORE[job_id].copy()

    path = get_job_metadata_path(job_id)
    if not path.exists():
        raise FileNotFoundError(f"Job {job_id} not found.")

    with path.open("r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise RuntimeError(f"Job file for {job_id} is empty.")

    try:
        job = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Job file for {job_id} is invalid JSON: {e}")

    with JOB_STORE_LOCK:
        JOB_STORE[job_id] = job.copy()

    return job.copy()


def save_job(job_id: str, job_data: dict) -> None:
    """
    Update memory first, then best-effort disk persistence.
    """
    with JOB_STORE_LOCK:
        JOB_STORE[job_id] = job_data.copy()

    try:
        _persist_job_to_disk(job_id, job_data)
    except Exception as e:
        # Do not break live polling because of disk-write issues
        print(f"[{job_id}] Warning: failed to persist job file: {e}")


def update_job_status(job_id: str, status: str, message: str = "") -> None:
    job = load_job(job_id)
    job["status"] = status
    job["message"] = message
    if status == "processing" and not job["started_at"]:
        job["started_at"] = _now()
    save_job(job_id, job)


def update_job_progress(
    job_id: str,
    progress: int,
    current_frame: int,
    total_frames: int,
    message: str = "",
) -> None:
    job = load_job(job_id)
    job["progress"] = progress
    job["current_frame"] = current_frame
    job["total_frames"] = total_frames
    job["message"] = message
    save_job(job_id, job)


def complete_job(job_id: str, result: dict) -> None:
    job = load_job(job_id)
    job["status"] = "completed"
    job["progress"] = 100
    job["message"] = "Processing completed successfully."
    job["output_video_path"] = result["output_video_path"]
    job["report_path"] = result["report_path"]
    job["summary"] = result["summary"]
    job["completed_at"] = _now()
    save_job(job_id, job)


def fail_job(job_id: str, error_message: str) -> None:
    job = load_job(job_id)
    job["status"] = "failed"
    job["message"] = "Processing failed."
    job["error"] = error_message
    job["completed_at"] = _now()
    save_job(job_id, job)