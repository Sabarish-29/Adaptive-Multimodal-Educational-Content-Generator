import { useState, useCallback } from 'react';
import { services } from '../../lib/api';
import { emitTelemetry, mark, markEnd } from '../../lib/telemetry';

interface ChunkEvent { part: string; done?: boolean; meta?: any }

export function useGenerateLessonStream(headers: Record<string,string>) {
  const [chunks, setChunks] = useState<string[]>([]);
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState<string|undefined>();
  const [active, setActive] = useState(false);
  const abortRef = useState<AbortController| null>(null)[0];

  const start = useCallback(async (payload: { learner_id: string; unit_id: string; objectives: string[] }) => {
    if(active) return;
    setChunks([]); setComplete(false); setError(undefined); setActive(true);
    const ac = new AbortController();
    // @ts-ignore
    abortRef.current = ac;
    mark('genStream');
    emitTelemetry({ type:'gen.stream.start' });
    try {
      const url = `${services.content}/v1/generate/lesson/stream`;
      const res = await fetch(url, { method:'POST', body: JSON.stringify(payload), headers: { 'Content-Type':'application/json', ...headers }, signal: ac.signal });
      if(!res.ok || !res.body){ throw new Error('stream_http_error'); }
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buffered = '';
      while(true){
        const { done, value } = await reader.read();
        if(done) break;
        buffered += dec.decode(value, { stream: true });
        let idx;
        while((idx = buffered.indexOf('\n')) !== -1){
          const line = buffered.slice(0, idx).trim();
          buffered = buffered.slice(idx+1);
          if(!line) continue;
          try {
            const evt: ChunkEvent = JSON.parse(line);
            if(evt.part){ setChunks(c=>[...c, evt.part]); emitTelemetry({ type:'gen.chunk', data:{ len: evt.part.length } }); }
            if(evt.done){ setComplete(true); }
          } catch {}
        }
      }
      markEnd('genStream','gen.stream.complete');
    } catch (e:any){
      if(e?.name === 'AbortError'){ emitTelemetry({ type:'gen.stream.abort' }); }
      else { setError(e?.message || 'stream_failed'); emitTelemetry({ type:'gen.stream.error', data:{ msg: e?.message } }); }
    } finally {
      setActive(false);
    }
  }, [active, headers]);

  const abort = useCallback(()=>{
    // @ts-ignore
    if(abortRef.current){ abortRef.current.abort(); }
  },[]);

  return { chunks, complete, error, active, start, abort };
}
