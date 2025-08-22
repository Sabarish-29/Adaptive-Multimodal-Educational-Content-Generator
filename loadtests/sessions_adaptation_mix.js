import http from 'k6/http';
import { check, sleep, Trend } from 'k6';

export let options = {
  vus: __ENV.VUS ? parseInt(__ENV.VUS) : 20,
  duration: __ENV.DURATION || '1m',
  thresholds: {
    'adaptation_latency{status:ok}': ['p(95)<800'],
  }
};

const ADAPT = __ENV.ADAPTATION_URL || 'http://localhost:8001';
const SESS = __ENV.SESSIONS_URL || 'http://localhost:8002';

let recLatency = new Trend('adaptation_latency');

export default function() {
  // 1. Start session (10% of iterations) else reuse pseudo id
  const sid = `sid-${__VU}-${Math.floor(Math.random()*100)}`;
  if (Math.random() < 0.1) {
    let resCreate = http.post(`${SESS}/v1/sessions`, JSON.stringify({ learner_id: 'L'+__VU, unit_id: 'U1'}), { headers: { 'Content-Type':'application/json'}});
    check(resCreate, { 'session create 201': r => r.status === 201 });
  }
  // 2. Call adaptation recommend-next directly
  const r = http.post(`${ADAPT}/v1/adaptation/recommend-next`, JSON.stringify({ learner_id: 'L'+__VU }), { headers:{'Content-Type':'application/json'}});
  const ok = r.status === 200;
  recLatency.add(r.timings.duration, { status: ok ? 'ok' : 'err'});
  check(r, { 'adaptation 200': _ => ok });
  sleep(0.2);
}
