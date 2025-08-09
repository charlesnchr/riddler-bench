export async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export const Api = {
  runs: () => fetchJSON('/api/runs'),
  aggregate: (run, mode = 'unique') => fetchJSON(`/api/aggregate${run ? `?run=${encodeURIComponent(run)}&mode=${mode}` : `?mode=${mode}`}`),
  files: (run) => fetchJSON(run ? `/api/files?run=${encodeURIComponent(run)}` : '/api/files'),
  detail: (file) => fetchJSON(`/api/detail?file=${encodeURIComponent(file)}`),
  questions: (run, mode = 'unique') => fetchJSON(run ? `/api/questions?run=${encodeURIComponent(run)}&mode=${mode}` : `/api/questions?mode=${mode}`),
  questionDetail: (key, run, mode = 'unique', qText) => fetchJSON(`/api/question_detail?${key ? `key=${encodeURIComponent(key)}&` : ''}${qText ? `q=${encodeURIComponent(qText)}&` : ''}${run ? `run=${encodeURIComponent(run)}&` : ''}mode=${mode}`),
}; 