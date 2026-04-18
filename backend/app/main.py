from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import OUTPUT_DIR, REPORT_DIR
from app.utils.file_utils import ensure_directories
from app.routes.upload import router as upload_router
from app.routes.jobs import router as jobs_router
from app.routes.results import router as results_router

ensure_directories()

app = FastAPI(title="Smart Drone Traffic Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(results_router, prefix="/api")

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
app.mount("/reports", StaticFiles(directory=str(REPORT_DIR)), name="reports")


@app.get("/")
def root():
    return {"message": "Smart Drone Traffic Analyzer backend is running."}


@app.get("/health")
def health():
    return {"status": "ok"}