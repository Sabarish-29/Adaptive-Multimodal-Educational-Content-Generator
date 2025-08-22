// Lightweight telemetry event dispatcher (Phase 4 scaffold)
// Collects UX & performance signals; can be swapped for external sink later.
export interface TelemetryEvent {
  type: string;         // canonical snake.case
  ts: number;           // epoch ms
  durMs?: number;       // optional duration
  data?: Record<string, any>; // small, sanitized key-value pairs
  rid?: string;         // request/page correlation id
  role?: string;        // user role (non-PII)
  anonId?: string;      // stable hash id (no raw PII)
  ver?: number;         // schema version
}

type Listener = (e: TelemetryEvent) => void;
const listeners = new Set<Listener>();
const SCHEMA_VERSION = 1;

// Sampling & feature flag
const ENABLED = (process.env.NEXT_PUBLIC_FEATURE_TELEMETRY || 'true') === 'true';
const SAMPLE_RATE = Number(process.env.NEXT_PUBLIC_TELEMETRY_SAMPLE_RATE || '1'); // 0..1

// Privacy: blocklist keys stripped from data (broad terms; lowercased contains match)
const BLOCKLIST = ['password','token','authorization','auth','secret','key','email','name'];

function sanitizeData(d: Record<string, any>){
  const out: Record<string, any> = {};
  for(const k of Object.keys(d||{})){
    const lower = k.toLowerCase();
    if(BLOCKLIST.some(b=> lower.includes(b))) continue;
    const v = d[k];
    if(typeof v === 'string') out[k] = v.length > 256 ? v.slice(0,256) : v; else out[k] = v;
  }
  return out;
}

export function onTelemetry(l: Listener){ listeners.add(l); return ()=>listeners.delete(l); }
export function emitTelemetry(e: Omit<TelemetryEvent,'ts'|'ver'>){
  if(!ENABLED) return;
  if(Math.random() > SAMPLE_RATE) return;
  // Basic validation / truncation
  const evt: TelemetryEvent = { ts: Date.now(), ver: SCHEMA_VERSION, ...e };
  if(evt.data) evt.data = sanitizeData(evt.data);
  listeners.forEach(l=>{ try { l(evt); } catch {} });
  if(typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('telemetry', { detail: evt }));
  enqueue(evt);
}

// Simple performance mark helper
const marks: Record<string, number> = {};
export function mark(name: string){ marks[name] = performance.now(); }
export function markEnd(name: string, type='perf'){ if(marks[name] != null){ const dur = performance.now() - marks[name]; emitTelemetry({ type, data:{ name }, durMs: dur }); delete marks[name]; } }

// Batching transport
interface BatchState { queue: TelemetryEvent[]; timer: any; flushing: boolean; retry: number; dropped: number; }
const state: BatchState = { queue: [], timer: null, flushing: false, retry: 0, dropped: 0 };
const MAX_BATCH = 50; // events per request
const FLUSH_MS = 5000;
const MAX_QUEUE = 1000; // global cap
let flushUrl: string | null = null;

export function configureTelemetry(opts: { endpoint: string }){ flushUrl = opts.endpoint; }

function enqueue(evt: TelemetryEvent){
  state.queue.push(evt);
  // Enforce global queue cap (drop oldest)
  if(state.queue.length > MAX_QUEUE){
    const over = state.queue.length - MAX_QUEUE;
    state.queue.splice(0, over);
    state.dropped += over;
  }
  if(state.queue.length >= MAX_BATCH) flush();
  else if(!state.timer) state.timer = setTimeout(()=>flush(), FLUSH_MS);
}

async function flush(){
  if(state.flushing) return;
  if(!state.queue.length) return;
  const batch = state.queue.splice(0, state.queue.length);
  if(state.timer){ clearTimeout(state.timer); state.timer = null; }
  if(!flushUrl){ return; }
  state.flushing = true;
  try {
    await fetch(flushUrl, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ events: batch }) });
  state.retry = 0;
  } catch (e){
  // retry with exponential backoff + jitter
  state.queue = [...batch, ...state.queue];
  state.retry = Math.min(state.retry + 1, 6);
  const backoff = Math.min(FLUSH_MS * Math.pow(2, state.retry), 60000);
  const jitter = backoff * (0.2 * Math.random());
  if(state.timer) clearTimeout(state.timer);
  state.timer = setTimeout(()=>flush(), backoff + jitter);
  } finally { state.flushing = false; }
}

// Test-only helper (no export in production build tooling can tree-shake if unused)
export function _forceFlushForTest(){ return (flush as any)(); }
export function flushPending(){ return flush(); }

// Lightweight stats for tests / debug overlay
export function telemetryStats(){
  return { queued: state.queue.length, retry: state.retry, dropped: state.dropped };
}

// Expose debug flush helper for tests/e2e (non-harmful in prod)
if(typeof window !== 'undefined'){
  // @ts-ignore
  (window as any).__telemetry_flush = flushPending;
}

// Flush on visibility hidden / page unload
if(typeof window !== 'undefined'){
  const handler = () => { if(state.queue.length && flushUrl){ navigator.sendBeacon?.(flushUrl, JSON.stringify({ events: state.queue.splice(0, state.queue.length) })); } };
  window.addEventListener('visibilitychange', ()=>{ if(document.visibilityState==='hidden') handler(); });
  window.addEventListener('pagehide', handler);
}

// Web Vitals integration placeholder (step 3)
export async function initWebVitals(){
  try {
    const { onCLS, onLCP, onINP, onFID, onTTFB } = await import('web-vitals');
    const report = (metric: any) => emitTelemetry({ type:'web_vital', data:{ name: metric.name, value: metric.value, rating: metric.rating } });
    onCLS(report); onLCP(report); onINP(report); onFID(report); onTTFB(report);
  } catch {}
}

// Anon identity generation (no PII). Stable per browser storage.
export function getAnonId(){
  if(typeof window === 'undefined') return undefined;
  try {
    const k = 'anon:id:v1';
    let v = localStorage.getItem(k);
    if(!v){ v = crypto.randomUUID().replace(/-/g,'').slice(0,16); localStorage.setItem(k, v); }
    return v;
  } catch { return undefined; }
}
