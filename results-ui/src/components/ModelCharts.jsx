import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line, CartesianGrid } from 'recharts';

export default function ModelCharts({ models }) {
  const data = models.map(m => ({
    model: m.model,
    accuracyPct: Number((m.accuracy * 100).toFixed(1)),
    latency: m.avgLatencyMs != null ? Math.round(m.avgLatencyMs) : null,
    coverage: m.coverage || 0,
    errorsPct: Number((m.errorRate * 100).toFixed(1)),
  }));

  return (
    <div className="grid" style={{ gridTemplateColumns: '1fr', gap: 16 }}>
      <div className="card">
        <h3>Accuracy by model</h3>
        <div style={{ width: '100%', height: 280 }}>
          <ResponsiveContainer>
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="model" angle={-20} textAnchor="end" height={60} tick={{ fill: '#8c90b3', fontSize: 12 }} />
              <YAxis tick={{ fill: '#8c90b3' }} domain={[0, 100]} />
              <Tooltip contentStyle={{ background: '#171a36', border: '1px solid rgba(255,255,255,0.08)', color: '#e7e9ff' }} />
              <Bar dataKey="accuracyPct" name="Accuracy %" fill="#7a5cff" radius={[6,6,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3>Avg latency by model</h3>
        <div style={{ width: '100%', height: 280 }}>
          <ResponsiveContainer>
            <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="model" angle={-20} textAnchor="end" height={60} tick={{ fill: '#8c90b3', fontSize: 12 }} />
              <YAxis tick={{ fill: '#8c90b3' }} />
              <Tooltip contentStyle={{ background: '#171a36', border: '1px solid rgba(255,255,255,0.08)', color: '#e7e9ff' }} />
              <Line type="monotone" dataKey="latency" name="Latency (ms)" stroke="#19c2ff" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3>Coverage and error rate</h3>
        <div style={{ width: '100%', height: 280 }}>
          <ResponsiveContainer>
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="model" angle={-20} textAnchor="end" height={60} tick={{ fill: '#8c90b3', fontSize: 12 }} />
              <YAxis yAxisId="left" orientation="left" tick={{ fill: '#8c90b3' }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: '#8c90b3' }} domain={[0, 100]} />
              <Tooltip contentStyle={{ background: '#171a36', border: '1px solid rgba(255,255,255,0.08)', color: '#e7e9ff' }} />
              <Bar yAxisId="left" dataKey="coverage" name="Distinct questions" fill="#7a5cff" radius={[6,6,0,0]} />
              <Bar yAxisId="right" dataKey="errorsPct" name="Errors %" fill="#ef4444" radius={[6,6,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
} 