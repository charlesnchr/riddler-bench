import { useEffect, useState } from 'react';
import { Api } from '../api';
import { displayModelName } from '../util';

export default function ResultDetail({ open, onClose, selection }) {
  const [items, setItems] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;
    async function load() {
      if (!selection) return;
      setLoading(true); setError(null);
      try {
        if (selection.type === 'question') {
          const data = await Api.questionDetail(selection.key, selection.run, selection.mode, selection.q);
          if (!ignore) {
            setMeta({ question: data.question, answer_ref: data.answer_ref, aliases: data.aliases, accuracy: data.accuracy, perModel: data.perModel });
            setItems(data.items || []);
          }
        } else if (selection.file) {
          const data = await Api.detail(selection.file);
          if (!ignore) setItems(data.items || []);
        } else if (selection.files && selection.files.length) {
          const all = [];
          for (const f of selection.files) {
            const data = await Api.detail(f);
            all.push(...(data.items || []));
          }
          if (!ignore) setItems(all);
        } else if (selection.model && selection.allFiles) {
          const all = [];
          for (const f of selection.allFiles) {
            const data = await Api.detail(f);
            all.push(...(data.items || []));
          }
          if (!ignore) setItems(all.filter(x => x.model === selection.model));
        } else {
          setItems([]);
        }
      } catch (e) { setError(String(e)); }
      finally { if (!ignore) setLoading(false); }
    }
    load();
    return () => { ignore = true; };
  }, [selection]);

  function headerTitle() {
    if (selection?.type === 'question') return selection?.title || 'Question';
    if (selection?.model) return displayModelName(selection.model);
    return selection?.title || 'Details';
  }

  return (
    <div className={`detail-panel ${open ? 'open' : ''}`}>
      <div className="detail-header">
        <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          <strong>{headerTitle()}</strong>
          {selection?.subtitle && <span className="tag">{selection.subtitle}</span>}
          {selection?.type === 'question' && meta?.accuracy != null && (
            <span className="badge ok">{(meta.accuracy * 100).toFixed(1)}% correct</span>
          )}
        </div>
        <button className="btn" onClick={onClose}>Close</button>
      </div>
      <div className="detail-body">
        {selection?.type === 'question' && meta && (
          <div className="card" style={{ marginBottom: 12 }}>
            <div className="section-title">Question</div>
            <div style={{ marginBottom: 6 }}>{meta.question}</div>
            <div className="section-title">Expected</div>
            <div className="row" style={{ gap: 8 }}>
              <span className="tag">answer_ref</span>
              <div>{meta.answer_ref || '-'}</div>
            </div>
            {Array.isArray(meta.aliases) && meta.aliases.length > 0 && (
              <div className="row" style={{ gap: 8, marginTop: 6 }}>
                <span className="tag">aliases</span>
                <div className="small">{meta.aliases.join(', ')}</div>
              </div>
            )}
            {Array.isArray(meta.perModel) && meta.perModel.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <div className="section-title">Per-model snapshot</div>
                <div className="pm-grid">
                  {meta.perModel.map(m => (
                    <div key={m.model} className="pm-row">
                      <span className="tag ellipsis" title={displayModelName(m.model)}>{displayModelName(m.model)}</span>
                      <span className={`badge ${m.is_correct ? 'ok' : 'err'}`}>{m.is_correct ? 'OK' : 'No'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {loading && <div>Loading…</div>}
        {error && <div className="badge err">{error}</div>}
        {!loading && !error && items.length === 0 && <div className="small">No items</div>}
        {!loading && !error && items.length > 0 && (
          <div className="grid" style={{ gap: 12 }}>
            {items.map((it) => (
              <div key={`${it.model}-${it.id}-${it._file}-${it._line}`} className="card">
                <div className="row" style={{ justifyContent: 'space-between' }}>
                  <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
                    <span className={`badge ${it.is_correct ? 'ok' : it.is_alias ? 'warn' : 'err'}`}>
                      {it.is_correct ? 'Correct' : it.is_alias ? 'Alias match' : 'Incorrect'}
                    </span>
                    <span className="tag">{displayModelName(it.model)}</span>
                    {it.latency_ms != null && <span className="metric" title="Latency in seconds">Latency: {(it.latency_ms/1000).toFixed(2)} s</span>}
                    {typeof it.fuzzy === 'number' && <span className="metric" title="Similarity score (0-100)">Similarity: {it.fuzzy}</span>}
                    {typeof it.input_tokens === 'number' && <span className="metric" title="Input tokens">In: {it.input_tokens}</span>}
                    {typeof it.output_tokens === 'number' && <span className="metric" title="Output tokens">Out: {it.output_tokens}</span>}
                    {typeof it.reasoning_tokens === 'number' && it.reasoning_tokens > 0 && <span className="metric warn" title="Reasoning tokens">Reason: {it.reasoning_tokens}</span>}
                  </div>
                  <span className="small">{it._file}:{it._line}</span>
                </div>
                <div className="section-title">Question</div>
                <div>{it.question}</div>
                <div className="section-title">Expected</div>
                <div className="row" style={{ gap: 8 }}>
                  <span className="tag">answer_ref</span>
                  <div>{it.answer_ref}</div>
                </div>
                {Array.isArray(it.aliases) && it.aliases.length > 0 && (
                  <div className="row" style={{ gap: 8, marginTop: 6 }}>
                    <span className="tag">aliases</span>
                    <div className="small">{it.aliases.join(', ')}</div>
                  </div>
                )}
                <div className="section-title">Model Answer</div>
                <div className="code">{it.answer}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 