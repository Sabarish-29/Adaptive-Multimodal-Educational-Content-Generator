from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List
import re

router = APIRouter()

class QualityRequest(BaseModel):
    text: str = Field(..., max_length=20000)
    model: Optional[str] = None

class QualityResponse(BaseModel):
    chars: int
    words: int
    sentences: int
    avg_sentence_length: float
    flesch: float
    heading_count: int
    bullet_lines: int
    exclamations: int
    capitalization_ratio: float
    readability_flag: Optional[str] = None
    warnings: List[str]

def _flesch(words: int, sentences: int, syllables: int) -> float:
    if words == 0 or sentences == 0:
        return 0.0
    return 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)

def _syllable_estimate(word: str) -> int:
    word = word.lower()
    vowels = 'aeiouy'
    count = 0
    prev_v = False
    for ch in word:
        is_v = ch in vowels
        if is_v and not prev_v:
            count += 1
        prev_v = is_v
    if word.endswith('e') and count>1:
        count -= 1
    return max(count,1)

@router.post('/v1/quality/score', response_model=QualityResponse)
async def quality_score(req: QualityRequest):
    text = req.text.strip()
    chars = len(text)
    sentence_splits = re.split(r'[.!?]+\s+', text)
    sentences = len([s for s in sentence_splits if s.strip()]) or 1
    tokens = re.findall(r"[A-Za-z']+", text)
    words = len(tokens)
    syllables = sum(_syllable_estimate(w) for w in tokens)
    flesch = _flesch(words, sentences, syllables)
    avg_sentence_length = words / sentences if sentences else 0
    heading_count = len(re.findall(r'^#+\s+.+', text, flags=re.MULTILINE))
    bullet_lines = len(re.findall(r'^[-*+]\s+.+', text, flags=re.MULTILINE))
    exclamations = text.count('!')
    capitals = sum(1 for c in text if c.isupper())
    letters = sum(1 for c in text if c.isalpha()) or 1
    capitalization_ratio = capitals/letters
    warnings: List[str] = []
    readability_flag: Optional[str] = None
    if flesch < 40:
        readability_flag = 'hard'
        warnings.append('Low Flesch score (hard to read)')
    if avg_sentence_length > 30:
        warnings.append('Average sentence length high')
    if capitalization_ratio > 0.25:
        warnings.append('High uppercase ratio')
    if exclamations > 5:
        warnings.append('Many exclamation marks')
    return QualityResponse(
        chars=chars,
        words=words,
        sentences=sentences,
        avg_sentence_length=round(avg_sentence_length,2),
        flesch=round(flesch,2),
        heading_count=heading_count,
        bullet_lines=bullet_lines,
        exclamations=exclamations,
        capitalization_ratio=round(capitalization_ratio,3),
        readability_flag=readability_flag,
        warnings=warnings
    )
