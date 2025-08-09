export default function StatCard({ title, value, sub, badge }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div className="kpi">{value}</div>
        {badge && <span className={`badge ${badge.variant || ''}`}>{badge.label}</span>}
      </div>
      {sub && <div className="sub" style={{ marginTop: 6 }}>{sub}</div>}
    </div>
  );
} 