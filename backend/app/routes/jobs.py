import threading
import traceback

from fastapi import APIRouter, HTTPException

from app.schemas import JobStatusResponse
from app.services.job_service import (
    load_job,
    update_job_status,
    update_job_progress,
    complete_job,
    fail_job,
)
from app.services.video_processor import process_video

router = APIRouter()


def _run_processing(job_id: str):
    try:
        job = load_job(job_id)

        update_job_status(
            job_id,
            "processing",
            "Opening video and loading model...",
        )

        def updater(progress: int, current_frame: int, total_frames: int, message: str):
            print(f"[{job_id}] {progress}% | {current_frame}/{total_frames} | {message}", flush=True)
            update_job_progress(job_id, progress, current_frame, total_frames, message)

        result = process_video(job_id, job["input_video_path"], updater)
        complete_job(job_id, result)

    except Exception as e:
        # Print the FULL traceback so we can see exactly what line failed
        full_trace = traceback.format_exc()
        print(f"[{job_id}] Processing failed: {e}", flush=True)
        print(f"[{job_id}] Full traceback:\n{full_trace}", flush=True)
        fail_job(job_id, str(e))


@router.post("/process/{job_id}")
def start_processing(job_id: str):
    try:
        job = load_job(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if job["status"] == "processing":
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Already running.",
        }

    if job["status"] == "completed":
        return {
            "job_id": job_id,
            "status": "completed",
            "message": "Already completed.",
        }

    thread = threading.Thread(target=_run_processing, args=(job_id,), daemon=True)
    thread.start()

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Processing started.",
    }


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_status(job_id: str):
    try:
        job = load_job(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found.")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        current_frame=job["current_frame"],
        total_frames=job["total_frames"],
        message=job["message"],
        error=job.get("error"),
    )