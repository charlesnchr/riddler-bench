export default function ModelTable({ rows, onSelect }) {
  return (
    <div className="card table-card">
      <table className="table">
        <thead>
          <tr>
            <th>Model</th>
            <th>Accuracy</th>
            <th>Avg Fuzzy</th>
            <th>Avg Latency</th>
            <th>Errors</th>
            <th>Coverage</th>
            <th>Duplication</th>
            <th>Items</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.model} style={{ cursor: 'pointer' }} onClick={() => onSelect?.(r)}>
              <td>{r.model}</td>
              <td>
                <div className="row" style={{ gap: 10 }}>
                  <div style={{ width: 140 }} className="progress"><span style={{ width: `${(r.accuracy * 100).toFixed(1)}%` }} /></div>
                  <div>{(r.accuracy * 100).toFixed(1)}%</div>
                </div>
              </td>
              <td>{r.avgFuzzy?.toFixed(1) ?? '-'}</td>
              <td>{r.avgLatencyMs?.toFixed(0) ?? '-'} ms</td>
              <td>
                <span className={`badge ${r.errorRate > 0.2 ? 'err' : r.errorRate > 0.05 ? 'warn' : 'ok'}`}>
                  {(r.errorRate * 100).toFixed(1)}%
                </span>
              </td>
              <td>{r.coverage ?? '-'}</td>
              <td>{r.duplicationRatio ? r.duplicationRatio.toFixed(2) : '-'}</td>
              <td>{r.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 