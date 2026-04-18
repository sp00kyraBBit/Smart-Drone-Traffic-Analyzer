from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import UploadResponse
from app.utils.file_utils import (
    is_allowed_video,
    generate_job_id,
    get_upload_path,
    save_upload_file,
)
from app.services.job_service import create_job

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    if not is_allowed_video(file.filename):
        raise HTTPException(status_code=400, detail="Only .mp4 files are allowed.")

    job_id = generate_job_id()
    upload_path = get_upload_path(job_id, file.filename)

    await save_upload_file(file, upload_path)
    create_job(job_id, str(upload_path), file.filename)

    return UploadResponse(
        job_id=job_id,
        filename=file.filename,
        status="uploaded",
    )