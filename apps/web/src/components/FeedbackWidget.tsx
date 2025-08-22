import React from 'react';
import { Button } from './Button';
import { Modal } from './Modal';
import { Stack } from './Stack';
import { emitTelemetry, mark, markEnd } from '../lib/telemetry';
import { services } from '../lib/api';

interface Props {
  itemId: string;           // ID of the generated content item/bundle
  itemType?: string;        // e.g. 'lesson_bundle'
  learnerId?: string;       // optional
  compact?: boolean;
}

const TAGS = ['helpful','confusing','too_easy','too_hard','too_long','too_short','engaging','dry'];

export const FeedbackWidget: React.FC<Props> = ({ itemId, itemType='lesson_bundle', learnerId, compact }) => {
  const [open, setOpen] = React.useState(false);
  const [rating, setRating] = React.useState<number|undefined>(undefined); // +1 / -1
  const [tags, setTags] = React.useState<string[]>([]);
  const [comment, setComment] = React.useState('');
  const [submitting, setSubmitting] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);

  React.useEffect(()=>{ emitTelemetry({ type:'feedback.view', data:{ itemId, itemType } }); },[itemId,itemType]);

  const toggleTag = (t: string) => {
    setTags(prev => prev.includes(t) ? prev.filter(x=>x!==t) : [...prev, t]);
  };

  const submit = async () => {
    if(!rating) return;
    setSubmitting(true);
    try {
      mark('feedback');
      const payload = { itemId, itemType, rating, tags, comment: comment.trim() ? comment.trim() : undefined, learnerId };
      const res = await fetch(`${services.analytics}/v1/feedback`, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify(payload) });
      if(res.ok){
        emitTelemetry({ type:'feedback.submit', data:{ itemId, itemType, rating, tagCount: tags.length } });
        markEnd('feedback','feedback.dur');
        setSubmitted(true);
        setTimeout(()=> setOpen(false), 1200);
      }
    } finally { setSubmitting(false); }
  };

  const trigger = (
    <div style={{ display:'flex', gap:8, alignItems:'center' }}>
      <button aria-label="Thumbs up" onClick={()=>{ setRating(1); setOpen(true); }} style={btnStyle(rating===1)}>&#128077;</button>
      <button aria-label="Thumbs down" onClick={()=>{ setRating(-1); setOpen(true); }} style={btnStyle(rating===-1)}>&#128078;</button>
      {!compact && <span style={{ fontSize:11, opacity:.6 }}>Feedback</span>}
    </div>
  );

  return (
    <>
      {trigger}
  <Modal open={open} title="Content Feedback" onClose={()=>{ if(!submitting) { setOpen(false); } }}>
        <div style={{ padding:'4px 0' }}>
          {!submitted && (
            <Stack gap={12}>
              <div style={{ fontSize:12 }}>
                <strong style={{ color: rating===1 ? '#10B981' : rating===-1 ? '#EF4444' : '#6B7280' }}>{rating===1?'Positive':'Negative'}</strong> feedback for <code style={{ fontSize:11 }}>{itemId}</code>
              </div>
              <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
                {TAGS.map(t => (
                  <button key={t} onClick={()=>toggleTag(t)} style={tagStyle(tags.includes(t))}>{t.replace('_',' ')}</button>
                ))}
              </div>
              <textarea value={comment} onChange={e=>setComment(e.target.value)} placeholder="Optional comment (max 500 chars)" maxLength={500} style={{ width:'100%', minHeight:80, background:'#11151b', border:'1px solid #2A303B', borderRadius:6, color:'#E5E7EB', fontSize:12, padding:8, resize:'vertical' }} />
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <span style={{ fontSize:11, opacity:.5 }}>{tags.length} tag{tags.length!==1?'s':''} selected</span>
                <Button size="sm" disabled={submitting || !rating} onClick={submit}>{submitting? 'Submitting...' : 'Submit'}</Button>
              </div>
            </Stack>
          )}
          {submitted && <p aria-live="polite" style={{ fontSize:12, color:'#10B981', margin:'8px 0' }}>Thanks! Saved.</p>}
        </div>
      </Modal>
    </>
  );
};

function btnStyle(active: boolean): React.CSSProperties {
  return {
    background: active ? '#1F2937' : '#11151b',
    border: '1px solid #2A303B',
    width: 32,
    height: 32,
    borderRadius: 8,
    cursor: 'pointer',
    fontSize: 16,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: active ? '#FCD34D' : '#D1D5DB'
  };
}

function tagStyle(active: boolean): React.CSSProperties {
  return {
    fontSize: 11,
    padding: '4px 8px',
    borderRadius: 999,
    border: '1px solid ' + (active ? '#6366F1' : '#2A303B'),
    background: active ? '#1E1B4B' : '#161A21',
    cursor: 'pointer',
    color: active ? '#C7D2FE' : '#9CA3AF'
  };
}
