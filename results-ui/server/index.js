const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 4000;
const RESULTS_DIR = path.resolve(process.env.RESULTS_DIR || path.join(__dirname, '..', '..', 'results'));
const DATA_DIR = path.resolve(path.join(__dirname, '..', '..', 'data'));

// Serve static files from React build in production
const isProduction = process.env.NODE_ENV === 'production';
if (isProduction) {
  const buildPath = path.join(__dirname, '..', 'build');
  app.use(express.static(buildPath));
}

function findJsonlFiles(dir) {
  const results = [];
  function walk(current) {
    let entries;
    try { entries = fs.readdirSync(current, { withFileTypes: true }); }
    catch { return; }
    for (const entry of entries) {
      const full = path.join(current, entry.name);
      const rel = path.relative(RESULTS_DIR, full);
      if (entry.isDirectory()) {
        walk(full);
      } else if (entry.isFile() && entry.name.endsWith('.jsonl')) {
        results.push({ full, rel });
      }
    }
  }
  walk(dir);
  return results;
}

function parseJsonlFile(filePath) {
  let content = '';
  try { content = fs.readFileSync(filePath, 'utf8'); } catch { return []; }
  const lines = content.split(/\r?\n/);
  const items = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    try {
      const obj = JSON.parse(line);
      obj._file = path.relative(RESULTS_DIR, filePath);
      obj._line = i + 1;
      items.push(obj);
    } catch (e) {
      items.push({ _file: path.relative(RESULTS_DIR, filePath), _line: i + 1, parse_error: String(e), raw: line });
    }
  }
  return items;
}

function readJsonlData(filePath) {
  let content = '';
  try { content = fs.readFileSync(filePath, 'utf8'); } catch { return []; }
  const lines = content.split(/\r?\n/);
  const out = [];
  for (const line of lines) {
    const s = line.trim();
    if (!s) continue;
    try { out.push(JSON.parse(s)); } catch { /* ignore */ }
  }
  return out;
}

function questionKeyOf(item) {
  if (item == null) return 'unknown';
  if (item.id != null) return String(item.id);
  if (typeof item.question === 'string' && item.question.length > 0) return item.question;
  return 'unknown';
}

function aggregate(runFilter = null, mode = 'unique') {
  const allFiles = findJsonlFiles(RESULTS_DIR);
  const files = runFilter
    ? allFiles.filter(f => f.rel.startsWith(runFilter + path.sep))
    : allFiles;

  const fileToItems = new Map();
  for (const f of files) fileToItems.set(f.rel, parseJsonlFile(f.full));

  const items = Array.from(fileToItems.values()).flat();

  const modelsSet = new Set();
  const modelToAll = new Map();
  const modelToByQuestion = new Map();
  const questionToAll = new Map();
  const questionToByModel = new Map();
  const modelToRuns = new Map();

  for (const fRel of fileToItems.keys()) {
    const runName = fRel.split(path.sep)[0] || 'root';
    const arr = fileToItems.get(fRel);
    for (const it of arr) {
      const model = it.model || 'unknown';
      const qKey = questionKeyOf(it);
      modelsSet.add(model);

      if (!modelToAll.has(model)) modelToAll.set(model, []);
      modelToAll.get(model).push(it);

      if (!modelToByQuestion.has(model)) modelToByQuestion.set(model, new Map());
      if (!modelToByQuestion.get(model).has(qKey)) modelToByQuestion.get(model).set(qKey, []);
      modelToByQuestion.get(model).get(qKey).push(it);

      if (!questionToAll.has(qKey)) questionToAll.set(qKey, []);
      questionToAll.get(qKey).push(it);

      if (!questionToByModel.has(qKey)) questionToByModel.set(qKey, new Map());
      if (!questionToByModel.get(qKey).has(model)) questionToByModel.get(qKey).set(model, []);
      questionToByModel.get(qKey).get(model).push(it);

      if (!modelToRuns.has(model)) modelToRuns.set(model, new Set());
      modelToRuns.get(model).add(runName);
    }
  }

  // Determine intersection set if requested
  let intersectionKeys = null;
  if (mode === 'intersection') {
    const allKeys = Array.from(questionToByModel.keys());
    intersectionKeys = allKeys.filter(k => modelToByQuestion.size > 0 && Array.from(modelToByQuestion.keys()).every(m => questionToByModel.get(k)?.has(m)));
  }

  function pickUnique(records) {
    // Choose the last record (most recent) for deterministic behavior
    return records[records.length - 1];
  }

  function computeStatsForModel(model) {
    const byQ = modelToByQuestion.get(model) || new Map();
    let used = [];
    if (mode === 'all') {
      used = modelToAll.get(model) || [];
    } else if (mode === 'unique') {
      for (const [qKey, recs] of byQ.entries()) used.push(pickUnique(recs));
    } else if (mode === 'intersection') {
      for (const k of intersectionKeys || []) {
        const recs = byQ.get(k);
        if (recs && recs.length) used.push(pickUnique(recs));
      }
    }

    const count = used.length;
    const correct = used.filter(x => x.is_correct).length;
    const accuracy = count ? correct / count : 0;
    const fuzzyVals = used.map(x => typeof x.fuzzy === 'number' ? x.fuzzy : null).filter(v => v != null);
    const avgFuzzy = fuzzyVals.length ? fuzzyVals.reduce((a,b) => a+b, 0) / fuzzyVals.length : null;
    const latVals = used.map(x => typeof x.latency_ms === 'number' ? x.latency_ms : null).filter(v => v != null);
    const avgLatencyMs = latVals.length ? latVals.reduce((a,b) => a+b, 0) / latVals.length : null;
    const errorCount = used.filter(x => typeof x.answer === 'string' && x.answer.startsWith('<error:')).length;
    const errorRate = count ? errorCount / count : 0;

    // token usage averages if present (support multiple possible shapes)
    function get(obj, pathArr) {
      try {
        return pathArr.reduce((acc, k) => (acc && acc[k] !== undefined ? acc[k] : undefined), obj);
      } catch { return undefined; }
    }
    function getToken(it, kind) {
      const u = it.usage || it.token_usage || it.tokens || {};
      if (kind === 'in') {
        return coalesceNumber(
          it.input_tokens, it.input,
          u.input_tokens, u.input,
          it.prompt_tokens,
          u.prompt_tokens,
          get(u, ['prompt', 'tokens'])
        );
      }
      if (kind === 'out') {
        return coalesceNumber(
          it.output_tokens, it.output,
          u.output_tokens, u.output,
          it.completion_tokens,
          u.completion_tokens,
          get(u, ['completion', 'tokens'])
        );
      }
      if (kind === 'reason') {
        const r1 = coalesceNumber(
          it.reasoning_tokens,
          u.reasoning_tokens,
          it.reason_tokens,
          u.reason_tokens,
          get(u, ['prompt_tokens_details', 'reasoning_tokens']),
          get(u, ['completion_tokens_details', 'reasoning_tokens']),
          get(u, ['prompt', 'tokens_details', 'reasoning_tokens']),
          get(u, ['completion', 'tokens_details', 'reasoning_tokens'])
        );
        // Some providers split reasoning tokens across prompt/completion; try to sum if both exist
        const pDetail = coalesceNumber(
          get(u, ['prompt_tokens_details', 'reasoning_tokens']),
          get(u, ['prompt', 'tokens_details', 'reasoning_tokens'])
        ) || 0;
        const cDetail = coalesceNumber(
          get(u, ['completion_tokens_details', 'reasoning_tokens']),
          get(u, ['completion', 'tokens_details', 'reasoning_tokens'])
        ) || 0;
        if (pDetail + cDetail > 0) return pDetail + cDetail;
        return r1;
      }
      return null;
    }
    function coalesceNumber(...vals) {
      for (let v of vals) {
        if (typeof v === 'number' && !Number.isNaN(v)) return v;
        if (typeof v === 'string') {
          const n = Number(v);
          if (!Number.isNaN(n)) return n;
        }
      }
      return null;
    }
    function avgToken(kind) {
      const arr = used.map(it => getToken(it, kind)).filter(v => v != null);
      return arr.length ? arr.reduce((a,b) => a+b, 0) / arr.length : null;
    }
    let avgInputTokens = avgToken('in');
    let avgOutputTokens = avgToken('out');
    const avgReasoningTokens = avgToken('reason');
    const avgTotalTokens = coalesceNumber(
      avgToken('total'),
      // derive from known fields if available
      (avgInputTokens != null && avgOutputTokens != null) ? (avgInputTokens + avgOutputTokens) : null
    );
    // Fallbacks: if no output but total exists, attribute to output
    if (avgOutputTokens == null && avgTotalTokens != null) {
      avgOutputTokens = (avgInputTokens != null) ? Math.max(0, avgTotalTokens - avgInputTokens) : avgTotalTokens;
    }

    const rawCount = (modelToAll.get(model) || []).length;
    const distinctQuestions = (modelToByQuestion.get(model) || new Map()).size;
    const duplicationRatio = distinctQuestions ? rawCount / distinctQuestions : 1;
    const runs = Array.from(modelToRuns.get(model) || []);

    return { model, count, accuracy, avgFuzzy, avgLatencyMs, errorRate, coverage: distinctQuestions, rawCount, duplicationRatio, runsCount: runs.length, runs, avgInputTokens, avgOutputTokens, avgReasoningTokens };
  }

  // Files per model
  const filesByModel = {};
  for (const f of files) {
    const fileItems = fileToItems.get(f.rel) || [];
    const modelsInFile = new Set(fileItems.map(x => x.model || 'unknown'));
    for (const m of modelsInFile) {
      if (!filesByModel[m]) filesByModel[m] = [];
      filesByModel[m].push(f.rel);
    }
  }

  // Build models list
  const models = Array.from(modelsSet).map(computeStatsForModel);

  // Build questions list: include ALL questions with aggregated accuracy under mode
  const questions = [];
  const chosenKeys = mode === 'intersection' ? (intersectionKeys || []) : Array.from(questionToAll.keys());
  for (const k of chosenKeys) {
    const byModel = questionToByModel.get(k) || new Map();
    let pool = [];
    for (const [m, recs] of byModel.entries()) {
      if (mode === 'all') pool.push(...recs);
      else pool.push(pickUnique(recs));
    }
    const count = pool.length;
    const correct = pool.filter(x => x.is_correct).length;
    const accuracy = count ? correct / count : 0;
    const any = pool[0] || questionToAll.get(k)?.[0] || null;
    const question = any?.question || '(unknown)';
    questions.push({ key: k, question, count, accuracy });
  }

  const runs = Array.from(new Set(files.map(f => f.rel.split(path.sep)[0]).filter(Boolean)));

  return { runs, models, questions, filesByModel, files: files.map(f => f.rel), mode };
}

app.get('/api/runs', (req, res) => {
  const allFiles = findJsonlFiles(RESULTS_DIR);
  const runs = Array.from(new Set(allFiles.map(f => f.rel.split(path.sep)[0]).filter(Boolean)));
  res.json({ runs, base: RESULTS_DIR });
});

app.get('/api/files', (req, res) => {
  const run = req.query.run || null;
  const allFiles = findJsonlFiles(RESULTS_DIR).map(f => f.rel);
  const files = run ? allFiles.filter(rel => rel.startsWith(run + path.sep)) : allFiles;
  res.json({ files });
});

app.get('/api/detail', (req, res) => {
  const rel = req.query.file;
  if (!rel) return res.status(400).json({ error: 'file is required' });
  const full = path.join(RESULTS_DIR, rel);
  if (!full.startsWith(RESULTS_DIR)) return res.status(400).json({ error: 'invalid path' });
  try {
    const items = parseJsonlFile(full);
    res.json({ items });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

app.get('/api/aggregate', (req, res) => {
  const run = req.query.run || null;
  const mode = ['all','unique','intersection'].includes(req.query.mode) ? req.query.mode : 'unique';
  try {
    res.json(aggregate(run, mode));
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

app.get('/api/questions', (req, res) => {
  const run = req.query.run || null;
  const mode = ['all','unique','intersection'].includes(req.query.mode) ? req.query.mode : 'unique';
  try {
    const agg = aggregate(run, mode);
    res.json({ mode: agg.mode, questions: agg.questions });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

app.get('/api/question_detail', (req, res) => {
  const run = req.query.run || null;
  const mode = ['all','unique','intersection'].includes(req.query.mode) ? req.query.mode : 'unique';
  const keyParam = req.query.key; // may be id or full question text
  const qTextParam = req.query.q || null;
  if (!keyParam && !qTextParam) return res.status(400).json({ error: 'key or q is required' });

  try {
    const allFiles = findJsonlFiles(RESULTS_DIR);
    const files = run ? allFiles.filter(f => f.rel.startsWith(run + path.sep)) : allFiles;
    const fileToItems = new Map();
    for (const f of files) fileToItems.set(f.rel, parseJsonlFile(f.full));

    const modelToByQuestion = new Map();
    const modelSet = new Set();
    for (const [, arr] of fileToItems.entries()) {
      for (const it of arr) {
        const model = it.model || 'unknown';
        const qKey = questionKeyOf(it);
        if (!modelToByQuestion.has(model)) modelToByQuestion.set(model, new Map());
        if (!modelToByQuestion.get(model).has(qKey)) modelToByQuestion.get(model).set(qKey, []);
        modelToByQuestion.get(model).get(qKey).push(it);
        modelSet.add(model);
      }
    }

    function pickUnique(records) { return records[records.length - 1]; }

    const items = [];
    const perModel = [];
    for (const model of modelSet) {
      const byQ = modelToByQuestion.get(model) || new Map();
      let recs = undefined;
      if (keyParam) recs = byQ.get(keyParam);
      if ((!recs || recs.length === 0) && qTextParam) {
        for (const [, rs] of byQ.entries()) {
          if (rs && rs.length && rs[0]?.question === qTextParam) { recs = rs; break; }
        }
      }
      if ((!recs || recs.length === 0) && keyParam && !qTextParam) {
        for (const [, rs] of byQ.entries()) {
          if (rs && rs.length && rs[0]?.question === keyParam) { recs = rs; break; }
        }
      }
      if (!recs || recs.length === 0) continue;

      if (mode === 'all') {
        items.push(...recs.map(r => ({ ...r })));
        const last = recs[recs.length - 1];
        perModel.push({ model, is_correct: !!last.is_correct, latency_ms: last.latency_ms ?? null, fuzzy: last.fuzzy ?? null });
      } else {
        const chosen = pickUnique(recs);
        items.push({ ...chosen });
        perModel.push({ model, is_correct: !!chosen.is_correct, latency_ms: chosen.latency_ms ?? null, fuzzy: chosen.fuzzy ?? null });
      }
    }

    const count = items.length;
    const correct = items.filter(x => x.is_correct).length;
    const accuracy = count ? correct / count : 0;

    let question = qTextParam || '(unknown)';
    let answer_ref = null;
    let aliases = [];
    for (const it of items) {
      if (it.question && question === '(unknown)') question = it.question;
      if (it.answer_ref && !answer_ref) answer_ref = it.answer_ref;
      if (Array.isArray(it.aliases) && it.aliases.length && aliases.length === 0) aliases = it.aliases;
      if (question !== '(unknown)' && answer_ref && aliases.length) break;
    }

    res.json({ key: keyParam || null, q: qTextParam || null, run: run || null, mode, question, answer_ref, aliases, count, correct, accuracy, items, perModel });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

app.get('/api/quiz', (req, res) => {
  try {
    const mode = req.query.mode || 'random';
    const limit = Math.max(1, Math.min(20, parseInt(req.query.limit || '8', 10)));

    // Check for curated quiz mode
    const curatedFile = path.join(DATA_DIR, 'quiz_try_yourself.jsonl');
    const hasCurated = fs.existsSync(curatedFile);

    if (mode === 'curated' && hasCurated) {
      // Use pre-designed curated questions with fixed options
      const dataset = readJsonlData(curatedFile);
      const quiz = dataset.map((q, idx) => {
        if (!q.question || !q.answer || !Array.isArray(q.options)) return null;
        const correctIndex = q.options.indexOf(q.answer);
        return { id: idx + 1, question: q.question, options: q.options, correctIndex };
      }).filter(q => q !== null);
      return res.json({ items: quiz, source: 'quiz_try_yourself.jsonl', mode: 'curated' });
    }

    // Random mode: generate random quiz from benchmark data
    const primary = path.join(DATA_DIR, 'benchmark_oblique_harder.jsonl');
    const fallback = path.join(DATA_DIR, 'benchmark.jsonl');
    const existsPrimary = fs.existsSync(primary);
    const dataset = readJsonlData(existsPrimary ? primary : fallback);
    const byAnswer = new Map();
    const items = [];
    for (const it of dataset) {
      if (!it || !it.question || !it.answer_ref) continue;
      items.push({ question: it.question, answer_ref: it.answer_ref, aliases: Array.isArray(it.aliases) ? it.aliases : [] });
      if (!byAnswer.has(it.answer_ref)) byAnswer.set(it.answer_ref, true);
    }
    // pool of unique answers for distractors
    const allAnswers = Array.from(byAnswer.keys());
    function sample(array, k, excludeSet) {
      const out = [];
      const seen = new Set();
      while (out.length < k && seen.size < array.length) {
        const idx = Math.floor(Math.random() * array.length);
        const val = array[idx];
        if (excludeSet.has(val) || seen.has(val)) continue;
        seen.add(val); out.push(val);
      }
      return out;
    }
    // shuffle helper
    function shuffle(arr) { for (let i=arr.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [arr[i],arr[j]]=[arr[j],arr[i]];} return arr; }

    const selected = shuffle(items.slice()).slice(0, Math.min(limit, items.length));
    const quiz = selected.map((q, idx) => {
      const exclude = new Set([q.answer_ref]);
      const distractors = sample(allAnswers, 3, exclude);
      const opts = shuffle([q.answer_ref, ...distractors]);
      const correctIndex = opts.indexOf(q.answer_ref);
      return { id: idx + 1, question: q.question, options: opts, correctIndex };
    });
    res.json({ items: quiz, source: existsPrimary ? 'benchmark_oblique_harder.jsonl' : 'benchmark.jsonl', mode: 'random' });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

app.get('/api/health', (_req, res) => res.json({ ok: true }));

// Catch-all route - must be after all API routes
// This serves the React app for any route that doesn't match an API endpoint
if (isProduction) {
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'build', 'index.html'));
  });
}

app.listen(PORT, () => {
  console.log(`[results-ui] Server listening on http://localhost:${PORT}`);
  console.log('Environment:', isProduction ? 'production' : 'development');
  console.log('Results dir:', RESULTS_DIR);
}); 