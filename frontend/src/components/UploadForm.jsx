import { useState, useRef } from "react";
import { uploadVideo, startProcessing } from "../api/client";

export default function UploadForm({ onUploadSuccess, onError, disabled }) {
  const [file, setFile]       = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging]   = useState(false);
  const inputRef = useRef(null);

  const validate = (f) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".mp4")) {
      onError("Only .mp4 files are supported.");
      return;
    }
    onError("");
    setFile(f);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    validate(e.dataTransfer.files?.[0]);
  };

  const handleSubmit = async () => {
    if (!file) { onError("Please select an .mp4 file first."); return; }
    try {
      setUploading(true);
      onError("");
      const up = await uploadVideo(file);
      await startProcessing(up.job_id);
      onUploadSuccess(up.job_id);
      setFile(null);
    } catch (err) {
      onError(err?.response?.data?.detail || err?.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card">
      <p className="card-label">Upload Video</p>

      <input
        ref={inputRef}
        type="file"
        accept=".mp4,video/mp4"
        style={{ display: "none" }}
        onChange={(e) => validate(e.target.files?.[0])}
      />

      <div
        className={`upload-drop${dragging ? " dragging" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && !uploading && inputRef.current?.click()}
      >
        <div className="upload-drop-icon">
          <svg viewBox="0 0 24 24">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </div>
        <h3>Drop your video here</h3>
        <p>MP4 format only</p>
        {file && (
          <span className="file-selected-pill">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            {file.name}
          </span>
        )}
      </div>

      <button
        className="btn btn-secondary"
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={disabled || uploading}
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/>
        </svg>
        Browse file
      </button>

      <button
        className="btn btn-primary"
        type="button"
        onClick={handleSubmit}
        disabled={!file || uploading || disabled}
      >
        {uploading
          ? <><span className="spinner" /> Uploading…</>
          : "Analyze Video"
        }
      </button>
    </div>
  );
}