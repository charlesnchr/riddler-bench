export default function StatCard({ title, value, sub, badge, formatter }) {
  const display = typeof formatter === 'function' ? formatter(value) : value;
  return (
    <div className="card" style={{ display: 'block' }}>
      <h3>{title}</h3>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div className="kpi">{display}</div>
        {badge && <span className={`badge ${badge.variant || ''}`} style={{ alignSelf: 'center' }}>{badge.label}</span>}
      </div>
      {sub && <div className="sub" style={{ marginTop: 6 }}>{sub}</div>}
    </div>
  );
} 