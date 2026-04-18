export default function JobStatus({ statusData }) {
  if (!statusData) return null;

  const { status, progress, message, current_frame, total_frames, error } = statusData;

  const badgeClass = {
    uploaded:   "badge-uploaded",
    processing: "badge-processing",
    completed:  "badge-completed",
    failed:     "badge-failed",
  }[status] || "badge-uploaded";

  const fillClass = status === "completed" ? "pf-done" : status === "failed" ? "pf-error" : "";

  const labels = {
    uploaded:   "Uploaded",
    processing: "Processing",
    completed:  "Complete",
    failed:     "Failed",
  };

  return (
    <div className="card">
      <p className="card-label">Analysis Progress</p>

      <div className="status-top">
        <span className={`status-badge ${badgeClass}`}>
          <span className={`dot${status === "processing" ? " pulse" : ""}`} />
          {labels[status] || status}
        </span>
        <span style={{ fontSize: "0.82rem", color: "var(--text-2)", fontWeight: 500 }}>
          {progress || 0}%
        </span>
      </div>

      <div className="progress-track">
        <div
          className={`progress-fill ${fillClass}`}
          style={{ width: `${progress || 0}%` }}
        />
      </div>

      <div className="status-footer">
        <span className="status-msg">
          {status === "processing" && <span className="spinner" style={{ color: "var(--warning)" }} />}
          {message}
        </span>
        {total_frames > 0 && (
          <span className="frame-info">
            {(current_frame || 0).toLocaleString()} / {total_frames.toLocaleString()} frames
          </span>
        )}
      </div>

      {error && (
        <p style={{ marginTop: 10, fontSize: "0.82rem", color: "var(--danger)" }}>
          {error}
        </p>
      )}
    </div>
  );
}