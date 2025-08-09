export default function RunSelector({ runs, value, onChange }) {
  return (
    <select className="select" value={value || ''} onChange={(e) => onChange(e.target.value || null)}>
      <option value="">All runs</option>
      {runs.map((r) => (
        <option key={r} value={r}>{r}</option>
      ))}
    </select>
  );
} 