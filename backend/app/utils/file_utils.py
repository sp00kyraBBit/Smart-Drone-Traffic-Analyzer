import uuid
from pathlib import Path
from fastapi import UploadFile

from app.config import UPLOAD_DIR, OUTPUT_DIR, REPORT_DIR, JOB_DIR, ALLOWED_EXTENSIONS


def ensure_directories() -> None:
    for directory in [UPLOAD_DIR, OUTPUT_DIR, REPORT_DIR, JOB_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def is_allowed_video(filename: str) -> bool:
    suffix = Path(filename).suffix.lower()
    return suffix in ALLOWED_EXTENSIONS


def generate_job_id() -> str:
    return uuid.uuid4().hex[:12]


def get_upload_path(job_id: str, original_filename: str) -> Path:
    suffix = Path(original_filename).suffix.lower()
    return UPLOAD_DIR / f"{job_id}_input{suffix}"


def get_output_video_path(job_id: str) -> Path:
    return OUTPUT_DIR / f"{job_id}_annotated.mp4"


def get_report_path(job_id: str) -> Path:
    return REPORT_DIR / f"{job_id}_report.xlsx"


def get_job_metadata_path(job_id: str) -> Path:
    return JOB_DIR / f"{job_id}.json"


async def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    with destination.open("wb") as f:
        content = await upload_file.read()
        f.write(content)