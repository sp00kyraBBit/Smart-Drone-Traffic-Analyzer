export default function VideoPlayer({ videoUrl }) {
  if (!videoUrl) return null;

  return (
    <div className="card">
      <p className="card-label">Annotated Output</p>
      <div className="video-wrapper">
        <video
          key={videoUrl}
          controls
          autoPlay={false}
          playsInline
          preload="metadata"
          style={{
            width: "100%",
            display: "block",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--border)",
            background: "#111",
          }}
        >
          <source src={videoUrl} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      </div>
    </div>
  );
}