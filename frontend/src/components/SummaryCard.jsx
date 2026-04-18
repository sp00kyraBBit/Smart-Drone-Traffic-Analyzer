export default function SummaryCard({ summary }) {
  if (!summary) return null;

  return (
    <div className="card">
      <h2>Summary</h2>
      <div className="summary-grid">
        <div><strong>Total Vehicles:</strong> {summary.total_unique_vehicles}</div>
        <div><strong>Cars:</strong> {summary.car}</div>
        <div><strong>Trucks:</strong> {summary.truck}</div>
        <div><strong>Buses:</strong> {summary.bus}</div>
        <div><strong>Motorcycles:</strong> {summary.motorcycle}</div>
        <div><strong>Processing Time:</strong> {summary.processing_duration_sec}s</div>
      </div>
    </div>
  );
}