from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import time
from .main import db

router = APIRouter()

MAX_COMMENT_LEN = 500
ALLOWED_RATINGS = {1,2,3,4,5}
MAX_TAGS = 5

class FeedbackIn(BaseModel):
    itemId: str = Field(..., max_length=120)
    itemType: str = Field(..., max_length=40, description="e.g. lesson|content|session")
    rating: int
    tags: List[str] = Field(default_factory=list)
    comment: Optional[str] = None
    anonId: Optional[str] = Field(None, max_length=64, description="Client-side anonymous id (already non-PII)")
    variant: Optional[str] = Field(None, max_length=32)
    model: Optional[str] = Field(None, max_length=64, description="Model or generator identifier")

    @validator('rating')
    def _rating_valid(cls, v):
        if v not in ALLOWED_RATINGS:
            raise ValueError('invalid_rating')
        return v

    @validator('tags', each_item=True)
    def _tag_len(cls, v):
        if len(v) > 24:
            raise ValueError('tag_too_long')
        return v

    @validator('tags')
    def _tags_limit(cls, v):
        if len(v) > MAX_TAGS:
            raise ValueError('too_many_tags')
        return v

    @validator('comment')
    def _comment_limit(cls, v):
        if v and len(v) > MAX_COMMENT_LEN:
            return v[:MAX_COMMENT_LEN]
        return v

class FeedbackDoc(FeedbackIn):
    ts: int
    _id: Optional[Any] = None

@router.post('/v1/feedback')
async def submit_feedback(payload: FeedbackIn):
    now = int(time.time()*1000)
    doc = payload.dict()
    doc['ts'] = now
    doc['itemType'] = doc['itemType'].lower()
    doc['tags'] = [t.lower() for t in doc['tags']]
    await db.feedback.insert_one(doc)
    return { 'ok': True, 'ts': now }

@router.get('/v1/feedback/item/{item_id}')
async def list_item_feedback(item_id: str, limit: int = Query(50, ge=1, le=500)):
    cursor = db.feedback.find({'itemId': item_id}).sort('ts', -1).limit(limit)
    out = []
    async for d in cursor:
        d['_id'] = str(d['_id'])
        out.append(d)
    return { 'itemId': item_id, 'feedback': out }

@router.get('/v1/feedback/aggregate')
async def aggregate_feedback(itemType: Optional[str] = None, window_hours: int = Query(24, ge=1, le=168)):
    since = int(time.time()*1000) - window_hours*3600*1000
    match: Dict[str, Any] = { 'ts': { '$gte': since } }
    if itemType:
        match['itemType'] = itemType.lower()
    pipeline = [
        { '$match': match },
        { '$group': { '_id': '$itemId', 'count': { '$sum': 1 }, 'avgRating': { '$avg': '$rating' } } },
        { '$sort': { 'count': -1 } },
        { '$limit': 200 }
    ]
    items = await db.feedback.aggregate(pipeline).to_list(length=200)
    tag_pipeline = [ { '$match': match }, { '$unwind': '$tags' }, { '$group': { '_id': '$tags', 'count': { '$sum': 1 } } }, { '$sort': { 'count': -1 } }, { '$limit': 50 } ]
    tag_rows = await db.feedback.aggregate(tag_pipeline).to_list(length=50)
    tags = [ { 'tag': t['_id'], 'count': t['count'] } for t in tag_rows ]
    return { 'since': since, 'windowHours': window_hours, 'items': items, 'tags': tags }
