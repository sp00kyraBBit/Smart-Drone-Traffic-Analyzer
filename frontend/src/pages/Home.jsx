import { useEffect, useRef, useState } from "react";
import UploadForm from "../components/UploadForm";
import JobStatus from "../components/JobStatus";
import VideoPlayer from "../components/VideoPlayer";
import SummaryTable from "../components/SummaryTable";
import DownloadButtons from "../components/DownloadButtons";
import { getJobResults, getJobStatus, buildAbsoluteUrl } from "../api/client";

export default function Home() {
  const [jobId, setJobId]           = useState("");
  const [statusData, setStatusData] = useState(null);
  const [results, setResults]       = useState(null);
  const [error, setError]           = useState("");
  const intervalRef = useRef(null);

  useEffect(() => () => { if (intervalRef.current) clearInterval(intervalRef.current); }, []);

  const startPolling = (id) => {
    if (intervalRef.current) clearInterval(intervalRef.current);

    const poll = async () => {
      try {
        const s = await getJobStatus(id);
        setStatusData(s);

        if (s.status === "completed") {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
          const r = await getJobResults(id);
          setResults(r);
        }

        if (s.status === "failed") {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
          setError(`Processing failed: ${s.error || "Check server logs for details."}`);
        }
      } catch (err) {
        if (err?.response?.status === 503) return;
        setError("Could not reach the server. Is the backend running?");
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 3000);
  };

  const handleUploadSuccess = (id) => {
    setError("");
    setResults(null);
    setJobId(id);
    setStatusData({
      job_id: id, status: "processing", progress: 0,
      current_frame: 0, total_frames: 0,
      message: "Upload complete. Starting analysis…", error: null,
    });
    startPolling(id);
  };

  const isProcessing = statusData?.status === "processing";

  return (
    <div className="page-wrapper">

      <header className="page-header">
        <div className="header-logo">
          <svg viewBox="0 0 24 24">
            <polygon points="23 7 16 12 23 17 23 7"/>
            <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
          </svg>
        </div>
        <div className="header-text">
          <h1>Drone Traffic Analyzer</h1>
          <p>Upload drone footage to automatically detect, track and count vehicles</p>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          {error}
        </div>
      )}

      <UploadForm
        onUploadSuccess={handleUploadSuccess}
        onError={setError}
        disabled={isProcessing}
      />

      {jobId && (
        <div className="job-id-bar">
          <span>Job ID</span>
          <code>{jobId}</code>
        </div>
      )}

      <JobStatus statusData={statusData} />

      <SummaryTable summary={results?.summary} />

      <VideoPlayer
        videoUrl={results?.output_video_url ? buildAbsoluteUrl(results.output_video_url) : ""}
      />

      <DownloadButtons
        reportUrl={results?.report_url ? buildAbsoluteUrl(results.report_url) : ""}
        videoUrl={results?.output_video_url ? buildAbsoluteUrl(results.output_video_url) : ""}
      />

    </div>
  );
}