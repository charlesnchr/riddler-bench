import { useEffect, useState } from 'react';
import { Api } from '../api';

export default function Quiz() {
  const [items, setItems] = useState([]);
  const [answers, setAnswers] = useState({});
  const [score, setScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true); setError(null); setScore(null); setAnswers({});
    try {
      const data = await Api.quiz(8);
      setItems(data.items || []);
    } catch (e) { setError(String(e)); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  function submit() {
    let correct = 0;
    for (const q of items) {
      if (answers[q.id] === q.correctIndex) correct++;
    }
    setScore({ correct, total: items.length });
  }

  return (
    <div className="card" style={{ padding: 16 }}>
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h3 style={{ margin: 0 }}>Try Yourself</h3>
        <div className="row" style={{ gap: 8 }}>
          <button className="btn" onClick={load}>Shuffle</button>
          <button className="btn primary" onClick={submit}>Submit</button>
        </div>
      </div>
      {loading && <div>Loading…</div>}
      {error && <div className="badge err">{error}</div>}
      {!loading && !error && items.length > 0 && (
        <div className="grid" style={{ gap: 12 }}>
          {items.map(q => (
            <div key={q.id} className="card">
              <div style={{ marginBottom: 8 }}><strong>Q{q.id}.</strong> {q.question}</div>
              <div className="grid" style={{ gap: 8 }}>
                {q.options.map((opt, idx) => {
                  const selected = answers[q.id] === idx;
                  const isCorrect = score && idx === q.correctIndex;
                  const isWrongSel = score && selected && idx !== q.correctIndex;
                  return (
                    <label key={idx} className={`row`} style={{ gap: 8, alignItems: 'center' }}>
                      <input
                        type="radio"
                        name={`q-${q.id}`}
                        checked={selected || false}
                        onChange={() => setAnswers({ ...answers, [q.id]: idx })}
                        disabled={!!score}
                      />
                      <span className={`tag ${isCorrect ? 'ok' : isWrongSel ? 'err' : ''}`} style={{ flex: 1 }}>{opt}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
      {score && (
        <div className="row" style={{ justifyContent: 'space-between', marginTop: 12 }}>
          <div className="badge ok">Score: {score.correct}/{score.total}</div>
          <button className="btn" onClick={load}>Try another set</button>
        </div>
      )}
    </div>
  );
} 