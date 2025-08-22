import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: __ENV.VUS ? parseInt(__ENV.VUS) : 10,
  duration: __ENV.DURATION || '30s'
};

const SESS = __ENV.SESSIONS_URL || 'http://localhost:8002';

export default function() {
  const res = http.post(`${SESS}/v1/sessions`, JSON.stringify({ learner_id: 'L'+__ITER, unit_id: 'U1' }), { headers: { 'Content-Type':'application/json' }});
  check(res, { 'create 201': r => r.status === 201 });
  sleep(0.5);
}
