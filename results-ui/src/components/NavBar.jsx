export default function NavBar({ runs, selectedRun, onRunChange, onRefresh, mode, onModeChange }) {
  return (
    <div className="topbar">
      <div className="brand">
        <div className="logo" />
        <div className="title">Riddler Bench – Results Explorer</div>
      </div>
      <div className="controls">
        <select className="select" value={mode} onChange={(e) => onModeChange(e.target.value)}>
          <option value="unique">Unique per question</option>
          <option value="all">All entries</option>
          <option value="intersection">Intersection across models</option>
        </select>
        <select className="select" value={selectedRun || ''} onChange={(e) => onRunChange(e.target.value || null)}>
          <option value="">All runs</option>
          {runs.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
        <button className="btn" onClick={onRefresh}>Refresh</button>
      </div>
    </div>
  );
} 