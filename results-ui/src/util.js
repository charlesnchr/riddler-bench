export function displayModelName(modelId) {
  if (!modelId || typeof modelId !== 'string') return modelId;
  // Remove provider prefix before ':'
  const afterColon = modelId.includes(':') ? modelId.split(':').pop() : modelId;
  // Remove company/family qualifier before '/'
  const afterSlash = afterColon.includes('/') ? afterColon.split('/').pop() : afterColon;
  return afterSlash;
} 