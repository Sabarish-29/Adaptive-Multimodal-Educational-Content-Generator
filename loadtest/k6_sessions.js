import http from 'k6/http';
import { Trend } from 'k6/metrics';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-vus',
      vus: __ENV.VUS ? parseInt(__ENV.VUS) : 10,
      duration: __ENV.DURATION || '1m'
    }
  }
};

const createLatency = new Trend('session_create_latency');
const eventLatency = new Trend('session_event_latency');

const BASE = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // create session
  const createStart = Date.now();
  let res = http.post(`${BASE}/v1/sessions`, JSON.stringify({ learner_id: 'k6L', unit_id: 'u1'}), { headers: { 'Content-Type': 'application/json' }});
  createLatency.add(Date.now() - createStart);
  check(res, { 'session created': (r) => r.status === 201 });
  if (res.status !== 201) { sleep(1); return; }
  const sid = res.json('session_id');
  // post event
  const evStart = Date.now();
  let ev = http.post(`${BASE}/v1/sessions/${sid}/events`, JSON.stringify({ type:'x', timestamp: new Date().toISOString(), payload: {} }), { headers: { 'Content-Type': 'application/json' }});
  eventLatency.add(Date.now() - evStart);
  check(ev, { 'event accepted': (r) => r.status === 202 });
  sleep(0.2);
}
