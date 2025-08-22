import { useEffect, useRef, useState, useCallback } from 'react';
import { services, withRid } from '../../lib/api';
import { emitTelemetry, mark, markEnd } from '../../lib/telemetry';

interface LiveEvent { [k: string]: any; }

export function useLiveSession(headers: Record<string,string>, learnerId: string, unitId: string){
  const [sessionId, setSessionId] = useState<string>('');
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [lastFreshTs, setLastFreshTs] = useState<number | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const reqId = headers['X-Request-ID'];
  const retryRef = useRef(0);

  const start = useCallback(async () => {
    mark('startSession');
    const res = await fetch(`${services.sessions}/v1/sessions`, { method:'POST', headers: { 'Content-Type':'application/json', ...headers }, body: JSON.stringify({ learner_id: learnerId, unit_id: unitId }) });
    if(!res.ok){
      markEnd('startSession', 'api');
      if(typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('rq:error', { detail: { error: new Error('Failed to start session') } }));
      emitTelemetry({ type:'session.start.error', data:{ status: res.status } });
      // Surface rate limit hint
      if(res.status === 429){
        const retryAfter = res.headers.get('retry-after');
        emitTelemetry({ type:'session.rate_limited', data:{ retryAfter } });
      }
      return;
    }
    const json = await res.json();
    markEnd('startSession', 'api');
    emitTelemetry({ type:'session.start', data:{ session_id: json.session_id } });
    setSessionId(json.session_id);
    const url = withRid(`${services.sessions}/v1/sessions/${json.session_id}/live`, reqId);
    if (esRef.current) esRef.current.close();
    const es = new EventSource(url);
    es.onmessage = e => {
      try { const data = JSON.parse(e.data); setEvents(prev => [...prev.slice(-24), data]); } catch {}
    };
    es.addEventListener('recommendation', (e: MessageEvent) => {
      try { const data = JSON.parse(e.data); setEvents(prev => [...prev.slice(-24), data]); if(!data.cached) setLastFreshTs(Date.now()); } catch {}
    });
    es.onerror = () => {
      es.close(); esRef.current = null;
      // Reconnect with capped exponential backoff
      const attempt = retryRef.current + 1;
      retryRef.current = attempt;
      const delay = Math.min(30000, 1000 * Math.pow(2, attempt - 1));
      emitTelemetry({ type:'session.sse.reconnect', data:{ attempt, delay } });
      setTimeout(()=>{
        if(!sessionId){ // session aborted externally
          retryRef.current = 0; return;
        }
        const es2 = new EventSource(url);
        es2.onmessage = es.onmessage!;
        es2.addEventListener('recommendation', (e: MessageEvent)=>{
          try { const data = JSON.parse(e.data); setEvents(prev => [...prev.slice(-24), data]); if(!data.cached) setLastFreshTs(Date.now()); } catch {}
        });
        es2.onerror = () => { es2.close(); esRef.current = null; };
        esRef.current = es2;
      }, delay);
    };
    esRef.current = es;
  }, [headers, learnerId, unitId, reqId]);

  useEffect(()=>()=>{ if (esRef.current) esRef.current.close(); },[]);

  return { start, sessionId, events, lastFreshTs };
}
