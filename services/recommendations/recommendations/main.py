from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple
import os, math, time, hashlib
from datetime import datetime

# Phase 5 Step 1-4: Data contract, heuristic scoring, experiment assignment, API endpoint

from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv('RECS_MONGODB_URI','mongodb://localhost:27017/edu')
MONGODB_DB = os.getenv('RECS_MONGODB_DB','edu')
client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

app = FastAPI(title="Recommendations Service", version="0.2.0")

# --- Data Models ---
class ContentMeta(BaseModel):
    id: str
    topics: List[str] = []
    difficulty: int = 3  # 1..5
    modality: str = "text"  # text|audio|video
    createdTs: int

class LearnerState(BaseModel):
    learnerId: str
    mastery: Dict[str, float] = {}  # topic -> 0..1
    recentContentIds: List[str] = []
    lastActiveTs: Optional[int] = None

class RecommendationItem(BaseModel):
    id: str
    score: float
    rank: int
    reason: List[str]
    variant: Optional[str] = None

class RecommendationResponse(BaseModel):
    learnerId: str
    variant: str
    items: List[RecommendationItem]
    generatedTs: int
    heuristic: Dict[str, float]
    algorithm: str

# --- In-memory stores (placeholder; real impl would query other services or a DB) ---
CONTENT_STORE: Dict[str, ContentMeta] = {}  # local cache
LEARNER_STATES: Dict[str, LearnerState] = {}  # in-memory write through cache
CACHE: Dict[str, Dict[str, any]] = {}  # key -> { ts, data }
METRICS = { 'cache_hits': 0, 'cache_misses': 0 }
MASTERY_SNAPSHOTS: Dict[str, List[Dict[str, any]]] = {}  # learnerId -> list of { ts, mastery }

RECS_ENABLED = (os.getenv('RECOMMENDATIONS_ENABLED', 'true').lower() == 'true')
CACHE_TTL_MS = int(os.getenv('RECS_CACHE_TTL_MS','180000'))  # 3 min default
API_TIMEOUT_MS = int(os.getenv('RECS_TIMEOUT_MS','200'))

# Seed some demo content (idempotent)
async def _seed():
    if CONTENT_STORE:
        return
    # Attempt to load from DB; if empty, create demo set
    existing = await db.recs_content.count_documents({})
    if existing == 0:
        now = int(time.time()*1000)
        docs = []
        for i in range(1, 11):
            cdoc = {
                'id': f'c{i}',
                'topics': ["algebra" if i%2 else "geometry", "fractions" if i%3==0 else "numbers"],
                'difficulty': (i % 5) + 1,
                'modality': "video" if i % 4 ==0 else ("audio" if i %3==0 else "text"),
                'createdTs': now - i*86400000
            }
            docs.append(cdoc)
        if docs:
            await db.recs_content.insert_many(docs)
    cursor = db.recs_content.find({})
    async for doc in cursor:
        CONTENT_STORE[doc['id']] = ContentMeta(**doc)

# --- Experiment Assignment ---
# Simple deterministic hash partition (2 variants: control, explore)
EXPERIMENT_KEY = os.getenv("REC_EXPERIMENT_KEY", "rec_v1")
VARIANTS = ["control", "explore"]

def assign_variant(learner_id: str) -> str:
    h = hashlib.sha256(f"{EXPERIMENT_KEY}:{learner_id}".encode()).hexdigest()
    bucket = int(h[:8], 16) % len(VARIANTS)
    return VARIANTS[bucket]

# --- Heuristic Scoring (Step 3) ---
WEIGHTS = {
    'topic_gap': float(os.getenv('REC_W_TOPIC_GAP', '0.5')),
    'freshness': float(os.getenv('REC_W_FRESHNESS', '0.2')),
    'difficulty_match': float(os.getenv('REC_W_DIFF_MATCH', '0.2')),
    'diversity_penalty': float(os.getenv('REC_W_DIVERSITY_PEN', '0.1')),
}
SIMILARITY_WEIGHT = float(os.getenv('REC_W_SIMILARITY', '0.3'))  # used in explore variant

TARGET_DIFFICULTY = int(os.getenv('REC_TARGET_DIFFICULTY', '3'))
FRESHNESS_DECAY_DAYS = float(os.getenv('REC_FRESHNESS_DAYS', '30'))


def _topic_gap_score(learner: LearnerState, content: ContentMeta) -> float:
    if not content.topics: return 0.0
    # Gap is higher when mastery is lower; average (1 - mastery)
    gaps = []
    for t in content.topics:
        m = learner.mastery.get(t, 0.0)
        gaps.append(1.0 - max(0.0, min(1.0, m)))
    return sum(gaps)/len(gaps)


def _freshness_score(content: ContentMeta) -> float:
    age_days = (time.time()*1000 - content.createdTs) / 86400000
    # Exponential decay; newer -> closer to 1
    return math.exp(-age_days / FRESHNESS_DECAY_DAYS)


def _difficulty_match_score(content: ContentMeta) -> float:
    # Distance from target
    return 1 - (abs(content.difficulty - TARGET_DIFFICULTY) / 4)


def _diversity_penalty(learner: LearnerState, content: ContentMeta) -> float:
    # Penalize if content topics are subset of many recent items (simple check)
    if not learner.recentContentIds: return 0.0
    recent_topics = []
    for cid in learner.recentContentIds[-5:]:
        c = CONTENT_STORE.get(cid)
        if c: recent_topics.extend(c.topics)
    if not recent_topics: return 0.0
    overlap = sum(1 for t in content.topics if t in recent_topics)
    return overlap / max(1, len(content.topics))  # 0..1


def _similarity_score(learner: LearnerState, content: ContentMeta) -> float:
    # Simple topic gap-based similarity (higher if learner has low mastery on content topics)
    if not content.topics: return 0.0
    gaps = []
    for t in content.topics:
        gaps.append(1.0 - max(0.0, min(1.0, learner.mastery.get(t, 0.0))))
    if not gaps: return 0.0
    # Normalize by max possible sum (len(content.topics))
    return sum(gaps) / len(content.topics)

def score_content(learner: LearnerState, variant: str, content: ContentMeta) -> Tuple[float, List[str]]:
    # Optionally adjust weights per variant later
    topic_gap = _topic_gap_score(learner, content)
    freshness = _freshness_score(content)
    diff_match = _difficulty_match_score(content)
    div_pen = _diversity_penalty(learner, content)
    base_score = (
        topic_gap * WEIGHTS['topic_gap'] +
        freshness * WEIGHTS['freshness'] +
        diff_match * WEIGHTS['difficulty_match'] -
        div_pen * WEIGHTS['diversity_penalty']
    )
    similarity = 0.0
    if variant == 'explore':  # hybrid scoring branch (Step 14)
        similarity = _similarity_score(learner, content)
        base_score += similarity * SIMILARITY_WEIGHT
    reasons = []
    if topic_gap > 0.5: reasons.append('addresses_gap')
    if freshness > 0.7: reasons.append('fresh')
    if diff_match > 0.7: reasons.append('difficulty_fit')
    if div_pen > 0.6: reasons.append('low_diversity_penalty')
    if similarity > 0.5: reasons.append('similarity')
    return base_score, reasons

# --- API Endpoint (Step 2 + 3 + 4 integration) ---
@app.get('/v1/recommendations/{learner_id}', response_model=RecommendationResponse)
async def get_recommendations(learner_id: str, limit: int = 5, forceVariant: Optional[str] = None):
    if not RECS_ENABLED:
        return RecommendationResponse(learnerId=learner_id, variant='disabled', items=[], generatedTs=int(time.time()*1000), heuristic=WEIGHTS, algorithm='disabled')
    start = time.time()*1000
    cache_key = f"{learner_id}:{limit}"
    now_ms = int(time.time()*1000)
    cached = CACHE.get(cache_key)
    if cached and (now_ms - cached['ts'] < CACHE_TTL_MS):
        METRICS['cache_hits'] += 1
        return cached['data']
    METRICS['cache_misses'] += 1
    # Fetch or create blank learner state
    learner = LEARNER_STATES.get(learner_id)
    if not learner:
        doc = await db.recs_learners.find_one({'learnerId': learner_id})
        if doc:
            learner = LearnerState(**doc)
        else:
            learner = LearnerState(learnerId=learner_id, mastery={}, recentContentIds=[])
        LEARNER_STATES[learner_id] = learner
    allow_force = os.getenv('ALLOW_FORCE_VARIANT','0') == '1'
    variant = forceVariant if (allow_force and forceVariant in VARIANTS) else assign_variant(learner_id)
    scored: List[RecommendationItem] = []
    for c in CONTENT_STORE.values():
        if c.id in learner.recentContentIds[-10:]:
            continue  # skip very recent repeats
        s, reasons = score_content(learner, variant, c)
        scored.append(RecommendationItem(id=c.id, score=round(float(s),6), rank=-1, reason=reasons, variant=variant))
    scored.sort(key=lambda x: x.score, reverse=True)
    for i, item in enumerate(scored):
        item.rank = i + 1
    items = scored[:limit]
    algorithm = 'hybrid' if variant == 'explore' else 'heuristic'
    resp = RecommendationResponse(
        learnerId=learner_id,
        variant=variant,
        items=items,
        generatedTs=int(time.time()*1000),
        heuristic=WEIGHTS,
        algorithm=algorithm
    )
    # timeout guard
    if (time.time()*1000 - start) > API_TIMEOUT_MS:
        # skip caching if too slow to encourage re-compute
        return resp
    CACHE[cache_key] = { 'ts': now_ms, 'data': resp }
    return resp

# Simple endpoint to upsert learner mastery (utility)
class MasteryUpdate(BaseModel):
    mastery: Dict[str, float]
    recentContentIds: Optional[List[str]] = None

@app.post('/v1/recommendations/{learner_id}/state')
async def update_state(learner_id: str, payload: MasteryUpdate):
    st = LEARNER_STATES.get(learner_id)
    if not st:
        doc = await db.recs_learners.find_one({'learnerId': learner_id})
        st = LearnerState(**doc) if doc else LearnerState(learnerId=learner_id, mastery={})
    st.mastery.update({k: max(0.0, min(1.0, v)) for k,v in payload.mastery.items()})
    if payload.recentContentIds is not None:
        st.recentContentIds = payload.recentContentIds[-50:]
    LEARNER_STATES[learner_id] = st
    # Bust cache for this learner
    for k in list(CACHE.keys()):
        if k.startswith(f"{learner_id}:"): del CACHE[k]
    # Write-through persist
    await db.recs_learners.update_one({'learnerId': learner_id}, { '$set': st.dict() }, upsert=True)
    return { 'ok': True }

@app.post('/v1/recommendations/snapshots/run')
async def run_mastery_snapshot():
    """Capture current mastery for all learners (Step 10 batch snapshot)."""
    now = int(time.time()*1000)
    count = 0
    # Ensure we have loaded any unseen learners? (skip for simplicity)
    for lid, st in LEARNER_STATES.items():
        snap = { 'ts': now, 'mastery': st.mastery.copy() }
        arr = MASTERY_SNAPSHOTS.setdefault(lid, [])
        arr.append(snap)
        # keep last 24 snapshots
        if len(arr) > 24: arr[:] = arr[-24:]
        count += 1
    return { 'snapshotsCreated': count }

@app.get('/v1/recommendations/{learner_id}/snapshots')
async def list_snapshots(learner_id: str):
    return { 'learnerId': learner_id, 'snapshots': MASTERY_SNAPSHOTS.get(learner_id, []) }

@app.on_event('startup')
async def _startup():
    # Indexes
    await db.recs_content.create_index('id', unique=True)
    await db.recs_learners.create_index('learnerId', unique=True)
    await _seed()

@app.get('/healthz')
async def health():
    return { 'status': 'ok' }

@app.get('/metrics')
async def metrics():
    return { **METRICS, 'cache_size': len(CACHE) }
