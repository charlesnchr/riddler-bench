import { useEffect, useMemo, useState } from 'react';
import NavBar from './components/NavBar';
import StatCard from './components/StatCard';
import ModelTable from './components/ModelTable';
import QuestionTable from './components/QuestionTable';
import ResultDetail from './components/ResultDetail';
import ModelCharts from './components/ModelCharts';
import { Api } from './api';

export default function App() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [mode, setMode] = useState('unique');
  const [agg, setAgg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selection, setSelection] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);

  async function load(run, m = mode) {
    setLoading(true); setError(null);
    try {
      const [runsList, aggregate] = await Promise.all([
        Api.runs(),
        Api.aggregate(run || null, m)
      ]);
      setRuns(runsList.runs || []);
      setAgg(aggregate);
    } catch (e) { setError(String(e)); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(selectedRun, mode); }, [selectedRun, mode]);

  const modelRows = useMemo(() => {
    if (!agg) return [];
    return [...(agg.models || [])].sort((a, b) => b.accuracy - a.accuracy);
  }, [agg]);

  const questionRows = useMemo(() => {
    if (!agg) return [];
    return [...(agg.questions || [])].sort((a, b) => a.accuracy - b.accuracy);
  }, [agg]);

  const totals = useMemo(() => {
    if (!agg) return { models: 0, questions: 0, avgAccuracy: 0, bestModel: '-', mode: 'unique' };
    const models = agg.models?.length || 0;
    const questions = agg.questions?.length || 0;
    const avgAccuracy = agg.models?.reduce((s, m) => s + m.accuracy, 0) / Math.max(models, 1);
    const bestModel = [...(agg.models || [])].sort((a, b) => b.accuracy - a.accuracy)[0]?.model || '-';
    return { models, questions, avgAccuracy, bestModel, mode: agg.mode };
  }, [agg]);

  function openModelDetail(row) {
    if (!agg) return;
    const files = agg.filesByModel?.[row.model] || [];
    setSelection({ title: row.model, model: row.model, allFiles: files, subtitle: (selectedRun || 'all runs') + ` · ${mode}` });
    setDetailOpen(true);
  }

  function openQuestionDetail(q) {
    setSelection({ type: 'question', key: q.key, q: q.question, title: 'Question', subtitle: (selectedRun || 'all runs') + ` · ${mode}`, run: selectedRun || null, mode });
    setDetailOpen(true);
  }

  return (
    <div className={`app-shell`}>
      <NavBar
        runs={runs}
        selectedRun={selectedRun}
        onRunChange={setSelectedRun}
        onRefresh={() => load(selectedRun, mode)}
        mode={mode}
        onModeChange={setMode}
      />

      <div className={`main-wrap${detailOpen ? ' with-detail' : ''}`}>
        <div className={`container`}>
          {loading && <div className="card">Loading…</div>}
          {error && <div className="card"><span className="badge err">{error}</span></div>}
          {!loading && !error && (
            <>
              <div className="grid stats">
                <StatCard title="Models tested" value={totals.models} />
                <StatCard title="Questions (mode)" value={totals.questions} sub={totals.mode} />
                <StatCard title="Average accuracy" value={`${(totals.avgAccuracy * 100).toFixed(1)}%`} />
                <StatCard title="Best model" value={totals.bestModel} badge={{ label: 'Top', variant: 'ok' }} />
              </div>

              <div className="section-title">Model performance</div>
              <div>
                <ModelCharts models={modelRows} />
              </div>

              <div className="section-title">Models</div>
              <ModelTable rows={modelRows} onSelect={openModelDetail} />

              <div className="section-title">Questions (all included, hardest first)</div>
              <QuestionTable rows={questionRows} onSelect={openQuestionDetail} />
            </>
          )}
        </div>
        {detailOpen && <div className="right-spacer" aria-hidden="true" />}
      </div>

      <ResultDetail open={detailOpen} onClose={() => setDetailOpen(false)} selection={selection} />
    </div>
  );
} 