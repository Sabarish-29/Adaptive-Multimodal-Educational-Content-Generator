from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from .main import db  # reuse existing Mongo client
import hashlib, os, hmac, base64
from datetime import datetime
from math import floor

router = APIRouter()

class TelemetryEvent(BaseModel):
    type: str = Field(..., max_length=60)
    ts: int
    durMs: Optional[float] = None
    data: Optional[Dict[str, Any]] = None
    rid: Optional[str] = Field(None, max_length=64)
    role: Optional[str] = Field(None, max_length=32)
    anonId: Optional[str] = Field(None, max_length=64)
    ver: Optional[int] = 1

class TelemetryBatch(BaseModel):
    events: List[TelemetryEvent]

MAX_EVENTS = 500

@router.post('/v1/telemetry/events')
async def ingest_events(batch: TelemetryBatch):
    n = len(batch.events)
    if n > MAX_EVENTS:
        raise HTTPException(status_code=400, detail='too_many_events')
    now_ms = int(time.time()*1000)
    docs = []
    salt = os.getenv('PII_HASH_SALT','')
    for e in batch.events:
        if e.ts > now_ms + 10*60*1000:
            continue
        doc = e.dict()
        # Hash anonId with salt for extra privacy layering (optional)
        if doc.get('anonId') and salt:
            h = hmac.new(salt.encode(), doc['anonId'].encode(), hashlib.sha256).digest()
            doc['anonId'] = base64.urlsafe_b64encode(h)[:22].decode()
        # Defensive: drop large nested data
        if doc.get('data') and isinstance(doc['data'], dict):
            for k,v in list(doc['data'].items()):
                if isinstance(v, str) and len(v) > 512:
                    doc['data'][k] = v[:512]
        docs.append(doc)
    accepted = len(docs)
    if docs:
        await db.telemetry_events.insert_many(docs)
    return { 'accepted': accepted, 'received': n }


@router.get('/v1/telemetry/latest')
async def telemetry_latest(limit: int = Query(100, ge=1, le=500)):
    cursor = db.telemetry_events.find({}, sort=[('ts', -1)], limit=limit)
    out = []
    async for doc in cursor:
        doc['_id'] = str(doc['_id'])
        out.append(doc)
    return { 'events': out }


@router.get('/v1/telemetry/stats')
async def telemetry_stats(window_minutes: int = Query(60, ge=1, le=1440)):
    """Return per-type counts + latency stats with precise p95 (via count/skip strategy)."""
    since = int(time.time()*1000) - window_minutes*60*1000
    pipeline = [
        { '$match': { 'ts': { '$gte': since } } },
        { '$group': { '_id': '$type', 'count': { '$sum': 1 }, 'avgDur': { '$avg': '$durMs' }, 'maxDur': { '$max': '$durMs' }, 'durCount': { '$sum': { '$cond': [{ '$ifNull': ['$durMs', False] }, 1, 0] } } } },
        { '$sort': { 'count': -1 } }
    ]
    agg = await db.telemetry_events.aggregate(pipeline).to_list(length=500)
    stats = []
    alerts = []
    latency_alert_threshold_ms = int(os.getenv('TELEMETRY_ALERT_P95_MS', '2000'))
    for row in agg:
        t = row['_id']
        p95 = None
        if row.get('durCount'):
            # total durations count
            total = int(row['durCount'])
            # zero-based index of p95 element
            idx = floor(0.95 * (total - 1)) if total > 1 else 0
            cursor = db.telemetry_events.find({'type': t, 'ts': { '$gte': since }, 'durMs': { '$ne': None }}, { 'durMs': 1 }).sort('durMs', 1).skip(idx).limit(1)
            async for d in cursor:
                p95 = d.get('durMs')
        r = { 'type': t, 'count': row['count'], 'avgDur': row.get('avgDur'), 'maxDur': row.get('maxDur'), 'p95Dur': p95 }
        stats.append(r)
        if p95 and p95 >= latency_alert_threshold_ms:
            alerts.append({'type': t, 'metric': 'p95Dur', 'value': p95, 'threshold': latency_alert_threshold_ms})
    return { 'since': since, 'windowMinutes': window_minutes, 'types': stats, 'alerts': alerts }


async def _compute_current_hour_rollup():
    """Compute / upsert rollups for current UTC hour and generate alerts collection entries."""
    now = datetime.utcnow()
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    hour_start_ms = int(hour_start.timestamp()*1000)
    next_hour_ms = hour_start_ms + 3600*1000
    pipeline = [
        { '$match': { 'ts': { '$gte': hour_start_ms, '$lt': next_hour_ms } } },
        { '$group': { '_id': '$type', 'count': { '$sum': 1 }, 'avgDur': { '$avg': '$durMs' }, 'maxDur': { '$max': '$durMs' }, 'durCount': { '$sum': { '$cond': [{ '$ifNull': ['$durMs', False] }, 1, 0] } } } }
    ]
    agg = await db.telemetry_events.aggregate(pipeline).to_list(length=500)
    for row in agg:
        t = row['_id']
        p95 = None
        if row.get('durCount'):
            total = int(row['durCount'])
            idx = floor(0.95 * (total - 1)) if total > 1 else 0
            cursor = db.telemetry_events.find({'type': t, 'ts': { '$gte': hour_start_ms, '$lt': next_hour_ms }, 'durMs': { '$ne': None }}, { 'durMs': 1 }).sort('durMs', 1).skip(idx).limit(1)
            async for d in cursor:
                p95 = d.get('durMs')
        await db.telemetry_rollups.update_one(
            {'hourStart': hour_start_ms, 'type': t},
            {'$set': {'count': row['count'], 'avgDur': row.get('avgDur'), 'maxDur': row.get('maxDur'), 'p95Dur': p95, 'updatedAt': int(time.time()*1000)}},
            upsert=True
        )
        # alert persistence (optional)
        latency_alert_threshold_ms = int(os.getenv('TELEMETRY_ALERT_P95_MS', '2000'))
        if p95 and p95 >= latency_alert_threshold_ms:
            await db.telemetry_alerts.insert_one({
                'hourStart': hour_start_ms,
                'type': t,
                'metric': 'p95Dur',
                'value': p95,
                'threshold': latency_alert_threshold_ms,
                'ts': int(time.time()*1000)
            })
    return {'hourStart': hour_start_ms, 'types': len(agg)}


@router.post('/v1/telemetry/rollup/run')
async def telemetry_run_rollup():
    """Manually trigger current-hour rollup computation (useful for tests or ad-hoc)."""
    res = await _compute_current_hour_rollup()
    return res


@router.get('/v1/telemetry/rollups/hourly')
async def telemetry_hourly_rollups(hours: int = Query(24, ge=1, le=168)):
    since = int((datetime.utcnow().timestamp()*1000)) - hours*3600*1000
    cursor = db.telemetry_rollups.find({'hourStart': {'$gte': since}}).sort('hourStart', -1)
    out: Dict[int, Dict[str, Any]] = {}
    async for doc in cursor:
        hs = doc['hourStart']
        if hs not in out:
            out[hs] = {}
        out[hs][doc['type']] = { 'count': doc.get('count'), 'avgDur': doc.get('avgDur'), 'p95Dur': doc.get('p95Dur'), 'maxDur': doc.get('maxDur') }
    # transform to list sorted descending
    series = [ { 'hourStart': k, 'types': v } for k,v in sorted(out.items(), key=lambda kv: kv[0], reverse=True) ]
    return { 'hours': hours, 'rollups': series }


@router.get('/v1/recommendations/metrics')
async def recommendation_metrics(window_minutes: int = Query(60, ge=5, le=1440)):
    """Aggregate rec.* telemetry events into CTR & variant breakdown.
    rec.fetch -> data.count (items suggested)
    rec.impression -> data.ids (array length = impressions)
    rec.click -> each event counts as one click
    Acceptance ~ clicks / fetches, CTR ~ clicks / impressions.
    """
    since = int(time.time()*1000) - window_minutes*60*1000
    match_stage = { '$match': { 'ts': { '$gte': since }, 'type': { '$in': ['rec.fetch','rec.impression','rec.click'] } } }
    # Flatten metrics per event
    project = { '$project': {
        'variant': '$data.variant',
        'fetch': { '$cond': [ { '$eq': ['$type','rec.fetch'] }, 1, 0 ] },
        'fetch_items': { '$cond': [ { '$eq': ['$type','rec.fetch'] }, { '$ifNull': ['$data.count', 0] }, 0 ] },
        'impressions': { '$cond': [ { '$eq': ['$type','rec.impression'] }, { '$size': { '$ifNull': ['$data.ids', []] } }, 0 ] },
        'clicks': { '$cond': [ { '$eq': ['$type','rec.click'] }, 1, 0 ] }
    } }
    group_variant = { '$group': { '_id': '$variant', 'fetches': { '$sum': '$fetch' }, 'total_items': { '$sum': '$fetch_items' }, 'impressions': { '$sum': '$impressions' }, 'clicks': { '$sum': '$clicks' } } }
    variants = await db.telemetry_events.aggregate([match_stage, project, group_variant]).to_list(length=50)
    overall = { 'fetches': 0, 'total_items': 0, 'impressions': 0, 'clicks': 0 }
    out_variants = []
    for v in variants:
        fetches = v.get('fetches',0) or 0
        impressions = v.get('impressions',0) or 0
        clicks = v.get('clicks',0) or 0
        total_items = v.get('total_items',0) or 0
        overall['fetches'] += fetches; overall['impressions'] += impressions; overall['clicks'] += clicks; overall['total_items'] += total_items
        out_variants.append({
            'variant': v['_id'] or 'unknown',
            'fetches': fetches,
            'impressions': impressions,
            'clicks': clicks,
            'avg_items_per_fetch': (total_items / fetches) if fetches else 0,
            'acceptance': (clicks / fetches) if fetches else 0,
            'ctr': (clicks / impressions) if impressions else 0
        })
    overall_metrics = {
        **overall,
        'avg_items_per_fetch': (overall['total_items']/overall['fetches']) if overall['fetches'] else 0,
        'acceptance': (overall['clicks']/overall['fetches']) if overall['fetches'] else 0,
        'ctr': (overall['clicks']/overall['impressions']) if overall['impressions'] else 0
    }
    return { 'since': since, 'windowMinutes': window_minutes, 'overall': overall_metrics, 'variants': out_variants }
