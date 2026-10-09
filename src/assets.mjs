// Bounded downloads and binary buffers avoid base64/DOM/offline-document copies.
export function createAssetLoader(fetcher = fetch, concurrency = 3) {
 let active = 0; const waiting = [];
 async function part(path) {
  if (active >= concurrency) await new Promise(resolve => waiting.push(resolve));
  else active++;
  try {
   for (let attempt = 0; attempt < 2; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 30000);
    try {
     const response = await fetcher(path, { signal: controller.signal });
     if (!response.ok) throw Error(`City asset unavailable (${response.status}).`);
     return new Uint8Array(await response.arrayBuffer());
    } catch (error) { if (attempt === 1) throw error; }
    finally { clearTimeout(timer); }
   }
  } finally { const next = waiting.shift(); if (next) next(); else active--; }
 }
 return async paths => {
  if (!paths.length) throw Error('The city asset is missing.');
  const parts = await Promise.all(paths.map(part));
  const bytes = new Uint8Array(parts.reduce((sum, p) => sum + p.length, 0));
  let offset = 0; for (const p of parts) { bytes.set(p, offset); offset += p.length; }
  return bytes;
 };
}
export function chooseQuality({ requested, coarse = false, memory = 8, saveData = false }) {
 if (['low', 'balanced', 'high'].includes(requested)) return requested;
 return coarse || memory <= 4 || saveData ? 'low' : 'balanced';
}
