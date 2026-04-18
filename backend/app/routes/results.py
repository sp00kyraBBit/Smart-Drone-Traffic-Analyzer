from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas import ResultResponse
from app.services.job_service import load_job

router = APIRouter()


@router.get("/results/{job_id}", response_model=ResultResponse)
def get_results(job_id: str):
    try:
        job = load_job(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job has not completed yet.")

    output_name = Path(job["output_video_path"]).name
    report_name = Path(job["report_path"]).name

    return ResultResponse(
        job_id=job_id,
        status=job["status"],
        summary=job["summary"],
        output_video_url=f"/outputs/{output_name}",
        report_url=f"/reports/{report_name}",
    )


@router.get("/download/report/{job_id}")
def download_report(job_id: str):
    try:
        job = load_job(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found.")

    report_path = Path(job["report_path"])
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found.")

    return FileResponse(
        path=report_path,
        filename=report_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )