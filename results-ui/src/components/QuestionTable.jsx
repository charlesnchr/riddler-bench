import { useMemo, useState } from 'react';

export default function QuestionTable({ rows, onSelect }) {
  const [sort, setSort] = useState({ key: 'accuracy', dir: 'asc' });
  const sorted = useMemo(() => {
    const arr = [...rows];
    arr.sort((a, b) => {
      const va = a[sort.key] ?? 0;
      const vb = b[sort.key] ?? 0;
      return sort.dir === 'asc' ? (va - vb) : (vb - va);
    });
    return arr;
  }, [rows, sort]);

  function toggle(key) {
    setSort(s => ({ key, dir: s.key === key && s.dir === 'asc' ? 'desc' : 'asc' }));
  }

  function handleClick(q) {
    onSelect?.({ ...q, key: q.key || q.question, question: q.question });
  }

  return (
    <div className="card table-card">
      <table className="table">
        <thead>
          <tr>
            <th onClick={() => toggle('question')} style={{ cursor: 'pointer' }}>Question</th>
            <th onClick={() => toggle('accuracy')} style={{ cursor: 'pointer' }}>Accuracy</th>
            <th onClick={() => toggle('count')} style={{ cursor: 'pointer' }}>Attempts</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((q, idx) => (
            <tr key={q.key || q.question || idx} style={{ cursor: 'pointer' }} onClick={() => handleClick(q)}>
              <td style={{ maxWidth: 520 }}>{q.question}</td>
              <td>
                <div className="row" style={{ gap: 10 }}>
                  <div style={{ width: 140 }} className="progress"><span style={{ width: `${(q.accuracy * 100).toFixed(1)}%` }} /></div>
                  <div>{(q.accuracy * 100).toFixed(1)}%</div>
                </div>
              </td>
              <td>{q.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 