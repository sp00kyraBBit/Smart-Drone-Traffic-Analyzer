# Smart Drone Traffic Analyzer

An end-to-end web application that accepts drone footage as input and automatically detects, tracks, and counts vehicles using YOLOv8 and a custom counting pipeline. The system delivers an annotated output video, a live progress feed, and a multi-sheet Excel report.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Structure](#2-project-structure)
3. [Local Setup — Backend](#3-local-setup--backend)
4. [Local Setup — Frontend](#4-local-setup--frontend)
5. [Running the Full Stack](#5-running-the-full-stack)
6. [Architecture Overview](#6-architecture-overview)
7. [Tracking & Counting Methodology](#7-tracking--counting-methodology)
8. [Edge Case Handling](#8-edge-case-handling)
9. [Excel Report Structure](#9-excel-report-structure)
10. [Engineering Assumptions](#10-engineering-assumptions)
11. [Configuration Reference](#11-configuration-reference)

---

## 1. Prerequisites

### System Requirements

| Dependency | Minimum Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend build tooling |
| npm | 8+ | JavaScript package management |
| FFmpeg | 4.x+ | Re-encoding output video for browser playback |

FFmpeg must be available on your system `PATH`. Install it via your OS package manager:

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# macOS (Homebrew)
brew install ffmpeg

# Windows — download from https://ffmpeg.org/download.html and add to PATH
```

### Python Dependencies

All Python packages are declared in `requirements.txt`:

```
fastapi
uvicorn[standard]
python-multipart
opencv-python
ultralytics
pandas
openpyxl
numpy
python-dotenv
filelock
```

> **Note on `ultralytics`:** The first run will automatically download the `yolov8n.pt` model weights (~6 MB) from the Ultralytics CDN into your working directory. Ensure you have internet access on the first launch.

---

## 2. Project Structure

```
project-root/
│
├── app/                          # Python backend (FastAPI)
│   ├── main.py                   # Application entry point, mounts routers + static dirs
│   ├── config.py                 # All tunable constants (paths, thresholds, ROI, etc.)
│   ├── schemas.py                # Pydantic request/response models
│   │
│   ├── routes/
│   │   ├── upload.py             # POST /api/upload
│   │   ├── jobs.py               # POST /api/process/:id, GET /api/status/:id
│   │   └── results.py            # GET /api/results/:id, GET /download/report/:id
│   │
│   ├── services/
│   │   ├── video_processor.py    # Core pipeline orchestrator
│   │   ├── detector_tracker.py   # YOLOv8 + ByteTrack wrapper + Re-ID logic
│   │   ├── counter_service.py    # Stateful vehicle counting logic
│   │   ├── job_service.py        # In-memory + disk job state management
│   │   └── report_service.py     # Excel export (pandas + openpyxl)
│   │
│   └── utils/
│       ├── file_utils.py         # Path helpers, UUID generation, file saving
│       ├── video_utils.py        # OpenCV metadata, centroid, ROI, FFmpeg conversion
│       └── draw_utils.py         # OpenCV annotation helpers (boxes, overlays, ROI)
│
├── frontend/                     # React + Vite frontend
│   ├── src/
│   │   ├── main.jsx              # React DOM entry point
│   │   ├── App.jsx               # Root component
│   │   ├── styles.css            # Global design tokens + component styles
│   │   ├── api/client.js         # Axios API wrapper (uploadVideo, getJobStatus, etc.)
│   │   ├── pages/Home.jsx        # Top-level page: orchestrates polling & state
│   │   └── components/
│   │       ├── UploadForm.jsx    # Drag-and-drop file upload
│   │       ├── JobStatus.jsx     # Progress bar + status badge
│   │       ├── SummaryTable.jsx  # Detection summary stats grid
│   │       ├── VideoPlayer.jsx   # HTML5 video player for annotated output
│   │       └── DownloadButtons.jsx
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── uploads/                      # Uploaded input videos (auto-created)
├── outputs/                      # Annotated output videos (auto-created)
├── reports/                      # Excel reports (auto-created)
├── jobs/                         # Job metadata JSON files (auto-created)
│
├── local_test_pipeline.py        # CLI script to test the pipeline without the API
└── requirements.txt
```

---

## 3. Local Setup — Backend

### Step 1 — Clone the repository

```bash
git clone https://github.com/sp00kyraBBit/Smart-Drone-Traffic-Analyzer.git
cd backend
```

### Step 2 — Create and activate a virtual environment

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (CMD)
.venv\Scripts\Activate
```

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — (Optional) Create a `.env` file

The application runs without a `.env` file using defaults, but you can override settings:

```dotenv
# .env — all values are optional, shown with defaults
YOLO_MODEL_NAME=yolov8n.pt
CONFIDENCE_THRESHOLD=0.35
FRAME_SKIP=1
```

### Step 5 — Start the backend server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/health` to confirm the server is running.

### Optional: Run the pipeline from the command line

```bash
python local_test_pipeline.py
# When prompted, enter the path to an .mp4 file, e.g.: /path/to/traffic.mp4
```

This bypasses the API entirely and is useful for rapid testing or debugging.

---

## 4. Local Setup — Frontend

### Step 1 — Navigate to the frontend directory

```bash
cd frontend   # or wherever your package.json lives
```

### Step 2 — Install JavaScript dependencies

```bash
npm install
```

### Step 3 — Start the development server

```bash
npm run dev
```

The UI will be available at `http://localhost:5173` (or the next available port Vite selects). 

### Building for production

```bash
npm run build
# Static files will be output to dist/
```

---

## 5. Running the Full Stack

With both servers running simultaneously:

| Service | URL |
|---|---|
| React frontend | `http://localhost:5173` |
| FastAPI backend | `http://localhost:8000` |
| Interactive API docs (Swagger) | `http://localhost:8000/docs` |

**Typical workflow:**

1. Open the frontend in your browser.
2. Drag-and-drop or browse to select an `.mp4` file.
3. Click **Analyze Video** — the file is uploaded and processing begins immediately.
4. Watch the live progress bar as the backend processes frames.
5. When complete, the annotated video and detection summary appear automatically.
6. Download the Excel report or annotated video using the download buttons.

---

## 6. Architecture Overview

### Backend: FastAPI + Background Threads

The backend is a single-process FastAPI application. Processing is CPU-bound and potentially long-running, so it is deliberately offloaded to a **daemon background thread** rather than an async task or a separate worker process. This avoids blocking the event loop while keeping the deployment simple (no Celery, Redis, or worker queue required).

```
Browser
  │
  │  POST /api/upload          (async — saves file to disk, creates job record)
  │  POST /api/process/:id     (starts background thread, returns immediately)
  │  GET  /api/status/:id      (polls in-memory JOB_STORE — no disk I/O on hot path)
  │  GET  /api/results/:id     (returns summary + file URLs once status=completed)
  │
  ▼
FastAPI (main thread / event loop)
  │
  └──► threading.Thread (daemon=True)
         └──► video_processor.process_video()
                ├── DetectorTracker.process_frame()   ← YOLOv8 + ByteTrack
                ├── CounterService.update()            ← counting logic
                ├── OpenCV VideoWriter                 ← annotated frame output
                └── report_service.export_excel()      ← Excel on completion
```

### Job State Management

Job state lives in **two layers**:

1. **In-memory `JOB_STORE` dict** (protected by a `threading.Lock`) — the primary source of truth during processing. All status polling reads from this dict directly, making it extremely fast.
2. **JSON file on disk** (`jobs/<job_id>.json`) — a best-effort write-through backup. It allows jobs to survive a server restart, but status polling does **not** depend on it (disk I/O failures are swallowed with a warning log).

```python
# Simplified flow
def save_job(job_id, job_data):
    with JOB_STORE_LOCK:
        JOB_STORE[job_id] = job_data.copy()   # primary — always succeeds
    try:
        _persist_job_to_disk(job_id, job_data) # secondary — best-effort
    except Exception:
        pass
```

### Frontend: React Polling

The frontend uses a simple **3-second polling interval** via `setInterval`. There is no WebSocket or SSE connection. When the job transitions to `completed`, the interval is cleared and a single results fetch is triggered.

```
Home.jsx
  ├── onUploadSuccess(jobId)  → sets jobId in state, starts setInterval
  ├── poll()                  → GET /api/status/:id every 3 s
  │     ├── status=processing → update progress bar
  │     ├── status=completed  → clear interval, GET /api/results/:id
  │     └── status=failed     → clear interval, display error banner
  └── results                 → render SummaryTable + VideoPlayer + DownloadButtons
```

### Static File Serving

Annotated videos and Excel reports are served directly by FastAPI's `StaticFiles` mount (no additional web server needed):

```
/outputs/*  →  app/outputs directory
/reports/*  →  app/reports directory
```

---

## 7. Tracking & Counting Methodology

### Detection: YOLOv8n + ByteTrack

Each frame is passed to the YOLOv8n model using Ultralytics' built-in `.track()` method with `persist=True`. This enables **ByteTrack** — a multi-object tracker that maintains track IDs across frames using Kalman filtering and IoU-based assignment. Only four vehicle classes are considered: `car`, `truck`, `bus`, `motorcycle`.

Detections are filtered before being passed to the counter:

- **Confidence threshold:** `0.35` — detections below this score are discarded.
- **Minimum bounding-box area:** `800 px²` — filters out distant noise.
- **Maximum area ratio:** `> 15%` of frame area — rejects anomalous full-frame detections.
- **Maximum aspect ratio:** `> 4.5` — rejects wide-angle distortion artifacts (relaxed slightly for buses/trucks).

### Re-Identification (ReID)

ByteTrack occasionally loses track of a vehicle (occlusion, frame boundary exit) and re-assigns a **new** track ID when it reappears. Without correction, the counter would treat it as a brand-new vehicle and double-count it.

The `DetectorTracker` class maintains a **`_lost_tracks` registry**: when a track ID disappears from the active set, its last bounding box and class are stored with a `lost_frame` timestamp. When a new track ID appears, it is matched against lost tracks using **IoU (Intersection over Union)**:

```
new_bbox ──► compute_iou(new_bbox, lost_bbox)
              if iou > REID_IOU_THRESHOLD (0.35) AND same class
              AND frame_gap ≤ REID_MAX_LOST_FRAMES (45)
                 ──► remap new track_id → original canonical_id
```

All downstream logic — including the `CounterService` — operates exclusively on the `canonical_id`, which remains stable across re-identification events.

### Counting Logic

Counting is handled by `CounterService`, which is stateless with respect to YOLO and maintains its own per-vehicle history. A vehicle is counted once (and only once) when **either** of two criteria is satisfied:

| Criterion | Condition | Purpose |
|---|---|---|
| **Stable ROI** | `frames_seen ≥ 4` AND `frames_inside_roi ≥ 2` | Counts vehicles that move slowly through the scene or are already present |
| **Line cross** | Centroid crosses `y = 350` (configurable) | Counts vehicles that cross the reference line, regardless of frame count |

The `OR` logic ensures both slow-moving and fast-passing vehicles are captured reliably. Once a `canonical_id` is in the `counted_ids` set, no further counting events are emitted for it regardless of how many more frames it appears in.

### Region of Interest (ROI)

When `USE_ROI = True` (default), only vehicles whose centroid falls within the rectangle `(40, 5, 1220, 700)` contribute to the `frames_inside_roi` counter. This prevents vehicles parked at the extreme edges of the frame (often partially visible) from inflating the count. The ROI boundary is drawn in green on every annotated frame.

---

## 8. Edge Case Handling

### Double-Counting Prevention

Three independent layers guard against double-counting:

1. **`counted_ids` set:** Once a `canonical_id` is added to this set in `CounterService`, the guard `if canonical_id not in self.counted_ids` prevents any future counting event for that vehicle.
2. **ReID remapping:** The `_id_map` dict in `DetectorTracker` maps every raw YOLO `track_id` to its original `canonical_id`, so a re-appearing vehicle inherits the same identity that was already counted.
3. **Lost-track TTL:** Stale entries in `_lost_tracks` expire after `REID_MAX_LOST_FRAMES = 45` frames (~1.5 seconds at 30 fps), preventing a different vehicle from being mis-identified as a previously-seen one.

### Oversized / Distorted Detections

The `_should_reject()` method in `DetectorTracker` discards bounding boxes that are geometrically implausible:

- Area ratio > 15% of the frame total (catches full-frame false positives).
- Aspect ratio > 4.5 (catches horizontally-smeared detections from YOLO at low confidence).
- Slightly tighter thresholds for `bus` and `truck` since these classes are naturally larger.

### Frame Skip

When `FRAME_SKIP > 1` in `config.py`, the pipeline skips intermediate frames to increase processing speed. Skipped frames are written to the output video using the **last annotated frame** to maintain visual continuity and correct video duration. The frame counter still increments normally so timestamps remain accurate.

### Video Re-encoding

After OpenCV writes the annotated video using the `mp4v` codec, FFmpeg re-encodes it using `libx264` with the `+faststart` moov-atom flag. This is necessary because:
- `mp4v` is not universally supported in browsers.
- `+faststart` moves the metadata atom to the file header so the browser can begin playback before the entire file is downloaded.

The original temp file is deleted after a successful FFmpeg conversion.

### Concurrent Job Requests

All mutations to `JOB_STORE` are wrapped in `JOB_STORE_LOCK` (a `threading.Lock`). The processing thread and the HTTP polling thread read from the same dict safely. If a job is already `processing` or `completed`, the `POST /api/process/:id` endpoint returns early with an informational message rather than starting a duplicate thread.

### Disk Persistence Failures

Disk writes are treated as non-critical. If writing the JSON job file fails (e.g., disk full, permissions), only a warning is printed. The in-memory `JOB_STORE` continues to serve all live polling requests without interruption.

---

## 9. Excel Report Structure

The generated `.xlsx` report contains four sheets:

| Sheet | Contents |
|---|---|
| **Summary** | Aggregate totals: total vehicles, per-type counts, processing duration |
| **CountedVehicles** | One row per unique vehicle — the frame number and timestamp at which it was officially counted, plus the count reason (`line_cross` or `stable_roi`) |
| **VehicleTimeline** | Every detection event across all frames for all vehicles — the full spatial and temporal trail (frame index, timestamp, bbox coordinates, confidence, ROI flag, counted flag) |
| **RawDetectionLog** | Unfiltered raw log of every detection with all internal fields, including `reidentified` and `crossed_line` flags |

All sheets have auto-fitted column widths for readability.

---

## 10. Engineering Assumptions

1. **Input format is `.mp4` only.** Only MP4 files are accepted at the upload endpoint. This simplifies codec handling and browser compatibility. Adding additional formats (`.avi`, `.mov`, etc.) would require minimal changes to `ALLOWED_EXTENSIONS` in `config.py` and the frontend file input `accept` attribute.

2. **Single-job concurrency per server process.** The system is designed to handle one active processing job at a time in a single-process deployment. Running multiple simultaneous jobs on one instance would compete for CPU resources (YOLO inference is compute-intensive) and could degrade performance significantly. For production multi-job throughput, a task queue (e.g., Celery + Redis) should replace the threading model.

3. **Fixed counting-line Y coordinate.** The horizontal counting reference line is hardcoded at `y = 350` pixels (`COUNTING_LINE_COORDS`). This was chosen to bisect a typical drone-view road scene. For footage with a different camera angle or resolution, this value should be adjusted in `config.py`.

4. **Frame resolution is assumed to be approximately 1280×720.** The ROI (`40, 5, 1220, 700`), minimum box area (`800 px²`), and aspect ratio thresholds were tuned with this resolution in mind. Significantly different input resolutions may require tuning these constants.

5. **YOLOv8n (nano) model.** The nano variant was chosen for its speed on CPU hardware. If a GPU is available, or if higher accuracy is preferred over speed, swapping `YOLO_MODEL_NAME` to `yolov8s.pt` or `yolov8m.pt` is sufficient — no code changes required.

6. **Vehicle classes are fixed to four types.** Only `car`, `truck`, `bus`, and `motorcycle` are counted. Other COCO classes detected by YOLO (e.g., `bicycle`, `person`) are silently discarded. This is controlled by `ALLOWED_CLASSES` in `config.py`.

7. **No authentication.** The API is open with `allow_origins=["*"]` CORS policy. This is appropriate for local development but should be restricted before any public deployment.

8. **Polling interval is 3 seconds.** The frontend polls the status endpoint every 3 seconds. This is a deliberate balance between perceived responsiveness and unnecessary network load. For very short videos (< 10 seconds of processing), the first poll after upload will often already show `completed`.

9. **Job state is ephemeral across server restarts (with disk fallback).** In-memory state is the source of truth. The on-disk JSON backup allows job recovery after a restart in principle, but there is no automatic recovery mechanism — the job would need to be re-submitted. This is an acceptable trade-off for a development-focused deployment.

10. **FFmpeg is a runtime dependency, not a Python package.** `convert_to_browser_mp4()` shells out to FFmpeg via `subprocess.run()`. If FFmpeg is not installed, the annotated video will not be produced and the job will fail at the 99% mark with a `FileNotFoundError` or `CalledProcessError`.

---

## 11. Configuration Reference

All tunable parameters live in `app/config.py`:

| Constant | Default | Description |
|---|---|---|
| `YOLO_MODEL_NAME` | `yolov8n.pt` | YOLO model variant to load |
| `CONFIDENCE_THRESHOLD` | `0.35` | Minimum detection confidence score |
| `MIN_BOX_AREA` | `800` | Minimum bounding box area in pixels² |
| `FRAME_SKIP` | `1` | Process every Nth frame (1 = all frames) |
| `ALLOWED_CLASSES` | `{car, bus, truck, motorcycle}` | Vehicle types to detect and count |
| `MIN_STABLE_FRAMES` | `4` | Frames a track must be seen before stable-count |
| `MIN_ROI_FRAMES` | `2` | Frames inside ROI required for stable-count |
| `REID_IOU_THRESHOLD` | `0.35` | Minimum IoU to re-identify a lost track |
| `REID_MAX_LOST_FRAMES` | `45` | Max frames a track is held in the lost registry |
| `USE_ROI` | `True` | Whether to restrict counting to the ROI rectangle |
| `ROI` | `(40, 5, 1220, 700)` | Region of Interest as `(x1, y1, x2, y2)` |
| `COUNTING_LINE_COORDS` | `(300, 350, 1100, 350)` | Counting reference line as `(x1, y1, x2, y2)` |
