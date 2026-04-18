import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from pathlib import Path
import sys

# Add backend folder to path when running this script directly
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.utils.file_utils import ensure_directories
from app.services.video_processor import process_video


if __name__ == "__main__":
    ensure_directories()

    sample_video = input("Enter sample video path: ").strip()
    result = process_video(job_id="localtest001", input_video_path=sample_video)

    print("\nProcessing finished.\n")
    print("Output video:", result["output_video_path"])
    print("Report path:", result["report_path"])
    print("Summary:", result["summary"])