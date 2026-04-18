export default function SummaryTable({ summary }) {
  if (!summary) return null;

  const vehicles = [
    { icon: "🚗", label: "Cars",        value: summary.car },
    { icon: "🚛", label: "Trucks",      value: summary.truck },
    { icon: "🚌", label: "Buses",       value: summary.bus },
    { icon: "🏍", label: "Motorcycles", value: summary.motorcycle },
    { icon: "⏱", label: "Seconds to process", value: summary.processing_duration_sec },
  ];

  return (
    <div className="card">
      <p className="card-label">Detection Summary</p>

      <div className="stats-grid">
        <div className="stat-card stat-total">
          <span className="stat-num">{summary.total_unique_vehicles}</span>
          <p className="stat-lbl">Total unique vehicles detected</p>
        </div>

        {vehicles.map(({ icon, label, value }) => (
          <div key={label} className="stat-card">
            <span className="stat-icon">{icon}</span>
            <span className="stat-num">{value}</span>
            <p className="stat-lbl">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}