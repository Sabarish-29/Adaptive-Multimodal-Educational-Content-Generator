import { emitTelemetry, configureTelemetry, _forceFlushForTest, onTelemetry, telemetryStats } from '../lib/telemetry';

// Single fetch mock
const fetchMock = jest.fn(()=>Promise.resolve({ ok:true } as any));
// @ts-ignore
global.fetch = fetchMock;

beforeEach(()=>{
  fetchMock.mockClear();
  configureTelemetry({ endpoint: 'http://localhost/telemetry' });
});

test('emits telemetry and batches flush under size threshold', async () => {
  const received: any[] = [];
  const off = onTelemetry(e=>received.push(e));
  emitTelemetry({ type:'test.event', data:{ a:1 } });
  expect(received.length).toBe(1);
  expect(fetchMock).not.toHaveBeenCalled();
  await _forceFlushForTest();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  off();
});

test('flush triggers when max batch reached', async () => {
  for(let i=0;i<51;i++) emitTelemetry({ type:'test.event', data:{ i } });
  await Promise.resolve();
  expect(fetchMock).toHaveBeenCalled();
});

test('large string values truncated', async () => {
  const big = 'x'.repeat(500);
  let received: any = null;
  const off = onTelemetry(e=>{ if(e.type==='test.trunc') received = e; });
  emitTelemetry({ type:'test.trunc', data:{ note: big } });
  expect(received).not.toBeNull();
  expect(received.data.note.length).toBeLessThanOrEqual(256);
  off();
  await _forceFlushForTest();
});

test('telemetryStats reflects queue growth then flush', async () => {
  for(let i=0;i<5;i++) emitTelemetry({ type:'qstat', data:{ i } });
  const before = telemetryStats();
  expect(before.queued).toBeGreaterThanOrEqual(5);
  await _forceFlushForTest();
  const after = telemetryStats();
  expect(after.queued).toBe(0);
});
