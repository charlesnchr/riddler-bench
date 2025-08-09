import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line, CartesianGrid, Legend } from 'recharts';
import { displayModelName } from '../util';

export default function ModelCharts({ models, onModelClick }) {
  const data = models.map(m => ({
    model: m.model,
    label: displayModelName(m.model),
    accuracyPct: Number((m.accuracy * 100).toFixed(1)),
    latency: m.avgLatencyMs != null ? Math.round(m.avgLatencyMs) : null,
    coverage: m.coverage || 0,
    errorsPct: Number((m.errorRate * 100).toFixed(1)),
    inputTokens: Number(m.avgInputTokens ?? 0),
    outputTokens: Number(m.avgOutputTokens ?? 0),
    reasoningTokens: Number(m.avgReasoningTokens ?? 0),
  }));

  return (
    <div className="grid" style={{ gridTemplateColumns: '1fr', gap: 16 }}>
      <div className="card">
        <h3>Accuracy by model</h3>
        <div style={{ width: '100%', height: 280 }}>
          <ResponsiveContainer>
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="label" angle={-20} textAnchor="end" height={60} tick={{ fill: '#8c90b3', fontSize: 12 }} />
              <YAxis tick={{ fill: '#8c90b3' }} domain={[0, 100]} />
              <Tooltip contentStyle={{ background: '#171a36', border: '1px solid rgba(255,255,255,0.08)', color: '#e7e9ff' }} formatter={(v, n, p) => [v, displayModelName(p.payload.model)]} />
              <Bar dataKey="accuracyPct" name="Accuracy %" fill="#3ca4b8" radius={[6,6,0,0]} cursor="pointer" onClick={(_, index) => onModelClick?.(models[index])} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3>Avg latency by model</h3>
        <div style={{ width: '100%', height: 280 }}>
          <ResponsiveContainer>
            <LineChart data={data.map(d => ({ ...d, latencySec: d.latency != null ? d.latency/1000 : null }))} margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="label" angle={-20} textAnchor="end" height={60} tick={{ fill: '#8c90b3', fontSize: 12 }} />
              <YAxis tick={{ fill: '#8c90b3' }} />
              <Tooltip contentStyle={{ background: '#171a36', border: '1px solid rgba(255,255,255,0.08)', color: '#e7e9ff' }} formatter={(v, n, p) => [`${v} s`, displayModelName(p.payload.label)]} />
              <Line type="monotone" dataKey="latencySec" name="Latency (s)" stroke="#19c2ff" strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3>Token usage (avg per request)</h3>
        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="label" angle={-20} textAnchor="end" height={60} tick={{ fill: '#8c90b3', fontSize: 12 }} />
              <YAxis tick={{ fill: '#8c90b3' }} />
              <Tooltip contentStyle={{ background: '#171a36', border: '1px solid rgba(255,255,255,0.08)', color: '#e7e9ff' }} formatter={(v, n, p) => [v, `${n} · ${displayModelName(p.payload.model)}`]} />
              <Legend wrapperStyle={{ color: '#8c90b3' }} />
              <Bar dataKey="inputTokens" name="Input" stackId="tokens" fill="#58c7a8" radius={[0,0,0,0]} />
              <Bar dataKey="outputTokens" name="Output" stackId="tokens" fill="#3ca4b8" radius={[0,0,0,0]} />
              <Bar dataKey="reasoningTokens" name="Reasoning" stackId="tokens" fill="#7dd3fc" radius={[6,6,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3>Coverage and error rate</h3>
        <div style={{ width: '100%', height: 280 }}>
          <ResponsiveContainer>
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="label" angle={-20} textAnchor="end" height={60} tick={{ fill: '#8c90b3', fontSize: 12 }} />
              <YAxis yAxisId="left" orientation="left" tick={{ fill: '#8c90b3' }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: '#8c90b3' }} domain={[0, 100]} />
              <Tooltip contentStyle={{ background: '#171a36', border: '1px solid rgba(255,255,255,0.08)', color: '#e7e9ff' }} formatter={(v, n, p) => [v, displayModelName(p.payload.model)]} />
              <Bar yAxisId="left" dataKey="coverage" name="Distinct questions" fill="#3ca4b8" radius={[6,6,0,0]} />
              <Bar yAxisId="right" dataKey="errorsPct" name="Errors %" fill="#ef4444" radius={[6,6,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
} 