export default function DownloadButtons({ reportUrl, videoUrl }) {
  if (!reportUrl && !videoUrl) return null;

  return (
    <div className="card">
      <h2>Downloads</h2>
      <div className="download-row">
        {reportUrl && (
          <a href={reportUrl} download className="btn btn-primary" style={{ flex: "1", marginTop: 0, minWidth: 180 }}>
            📊 Download Excel Report
          </a>
        )}
        {videoUrl && (
          <a href={videoUrl} download className="btn btn-secondary" style={{ flex: "1", minWidth: 180 }}>
            🎬 Download Annotated Video
          </a>
        )}
      </div>
    </div>
  );
}