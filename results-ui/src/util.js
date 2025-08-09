export function displayModelName(modelId) {
  if (!modelId || typeof modelId !== 'string') return modelId;
  const parts = modelId.split(':');
  return parts[parts.length - 1];
} 