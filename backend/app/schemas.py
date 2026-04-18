from typing import Dict, Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    job_id: str
    filename: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    current_frame: int
    total_frames: int
    message: str
    error: Optional[str] = None


class ResultResponse(BaseModel):
    job_id: str
    status: str
    summary: Dict
    output_video_url: Optional[str] = None
    report_url: Optional[str] = None