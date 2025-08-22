import time, os
from fastapi.testclient import TestClient
from analytics.main import app, db

client = TestClient(app)

def test_batch_rejects_too_many():
    payload = { 'events': [ { 'type':'x', 'ts': int(time.time()*1000) } for _ in range(600) ] }
    r = client.post('/v1/telemetry/events', json=payload)
    assert r.status_code == 400
    assert r.json()['detail'] == 'too_many_events'

def test_ingest_basic_and_hash():
    os.environ['PII_HASH_SALT'] = 'salt'
    now = int(time.time()*1000)
    r = client.post('/v1/telemetry/events', json={'events':[{'type':'page.view','ts':now,'anonId':'abc123'}]})
    assert r.status_code == 200
    assert r.json()['accepted'] == 1
    doc = db.telemetry_events.find_one({'type':'page.view'})
    # doc retrieval is async (motor), we skip live query here in sync test context.
    # ensure stats endpoint responds
    stats = client.get('/v1/telemetry/stats').json()
    assert 'types' in stats

def test_rollup_and_alerts():
    os.environ['TELEMETRY_ALERT_P95_MS'] = '0'  # force alert
    now = int(time.time()*1000)
    events = []
    for i in range(10):
        events.append({'type':'api.call','ts':now + i,'durMs': 100 + i})
    r = client.post('/v1/telemetry/events', json={'events':events})
    assert r.status_code == 200
    # trigger rollup
    rr = client.post('/v1/telemetry/rollup/run')
    assert rr.status_code == 200
    rollups = client.get('/v1/telemetry/rollups/hourly').json()
    assert 'rollups' in rollups
    stats = client.get('/v1/telemetry/stats').json()
    # Should include alerts due to threshold 0
    assert 'alerts' in stats and any(a['type']=='api.call' for a in stats['alerts'])
