import React from 'react';
import { useHasMounted } from '../hooks/useHasMounted';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { Stack } from '../components/Stack';
import { JSONViewer } from '../components/JSONViewer';
import { AppShell } from '../components/layout/AppShell';
import { useTheme } from '../theme/ThemeContext';
import { Skeleton } from '../components/Skeleton';
import { useLearnerProfile } from '../hooks/data/useLearnerProfile';
import { useAnalyticsProgress } from '../hooks/data/useAnalyticsProgress';
import { useGenerateLesson } from '../hooks/data/useGenerateLesson';
import { useGenerateLessonStream } from '../hooks/data/useGenerateLessonStream';
import { useLiveSession } from '../hooks/data/useLiveSession';
import { Badge } from '../components/Badge';
import { Modal } from '../components/Modal';
import { useAuth } from '../auth/AuthContext';
import { useAuthHeaders } from '../auth/useAuthHeaders';
import { services } from '../lib/api';
import { emitTelemetry, mark, markEnd } from '../lib/telemetry';
import { FeedbackWidget } from '../components/FeedbackWidget';


function HomeInner() {
  const headers = useAuthHeaders();
  const { user } = useAuth();
  const [bundle, setBundle] = React.useState<any>(null);
  const [lastRequestId, setLastRequestId] = React.useState<string>('');
  const [globalRateRemaining, setGlobalRateRemaining] = React.useState<string>('');
  const { data: profile, isLoading: profileLoading } = useLearnerProfile('learner_demo', headers);
  const { data: progress, isLoading: progressLoading, refetch: refetchProgress } = useAnalyticsProgress('learner_demo', headers);
  const generateLesson = useGenerateLesson(headers);
  const streamGen = useGenerateLessonStream(headers);
  const [streamMode, setStreamMode] = React.useState(false);
  const { start: startLive, sessionId, events: recs, lastFreshTs } = useLiveSession(headers, 'learner_demo', 'unit_math_1');
  // Phase 5 Step 5: Recommendations panel
  const [recsPanel, setRecsPanel] = React.useState<any[] | null>(null);
  const [recsVariant, setRecsVariant] = React.useState<string>('');
  const [recsLoading, setRecsLoading] = React.useState(false);
  const [recsDisabled, setRecsDisabled] = React.useState<boolean>(()=>{
    if(typeof window === 'undefined') return false;
    return localStorage.getItem('recs:disabled') === '1';
  });
  const toggleRecs = ()=>{
    setRecsDisabled(v=>{
      const nv = !v; if(typeof window !== 'undefined'){ localStorage.setItem('recs:disabled', nv? '1':'0'); }
      return nv;
    });
  };
  const fetchRecs = async ()=>{
    if(!user || recsDisabled) return;
    setRecsLoading(true);
    try {
      const r = await fetch(`${services.recommendations}/v1/recommendations/${encodeURIComponent(user.id)}?limit=5`).then(r=>r.json());
      setRecsPanel(r.items||[]);
      setRecsVariant(r.variant||'');
  emitTelemetry({ type:'rec.fetch', data:{ variant: r.variant, count: (r.items||[]).length } });
    } finally { setRecsLoading(false); }
  };
  React.useEffect(()=>{ if(typeof window !== 'undefined' && user && !recsDisabled) fetchRecs(); },[user, recsDisabled]);
  // Impression telemetry when list changes
  React.useEffect(()=>{
    if(recsPanel && recsPanel.length){
  emitTelemetry({ type:'rec.impression', data:{ variant: recsVariant, ids: recsPanel.map(r=>r.id).slice(0,20) } });
    }
  },[recsPanel, recsVariant]);
  const [rateRemaining, setRateRemaining] = React.useState<string>('');
  const generate = async () => {
  mark('gen');
  const { data, headers: h } = await generateLesson.mutateAsync({ learner_id: 'learner_demo', unit_id: 'unit_math_1', objectives: ['addition basics'] });
  markEnd('gen','gen.dur');
    setBundle(data);
    setLastRequestId(h['x-request-id'] || '');
    const rl = h['x-ratelimit-remaining'];
    if (rl) { setRateRemaining(rl as string); setGlobalRateRemaining(rl as string); }
  };
  const fetchProgress = async () => { await refetchProgress(); };
  const startSession = async () => { await startLive(); };
  const { theme, toggle } = useTheme();
  const [showModal, setShowModal] = React.useState(false);
  const bundleId = bundle?.bundle_id || bundle?.id || 'latest_bundle';
  return (
  <AppShell title="Adaptive Platform" nav={[{label:'Home', href:'/'},{label:'Analytics', href:'/analytics'},{label:'Content', href:'/content'},{label:'Sessions', href:'/sessions'},{label:'Telemetry', href:'/telemetry'}]} right={<Button size="sm" variant="ghost" onClick={toggle}>{theme==='dark' ? 'Light' : 'Dark'}</Button>}>
    <div style={{ maxWidth:1200, margin:'0 auto', padding:32 }}>
      <h2 style={{ fontSize:24, margin:'0 0 8px' }}>Developer Console</h2>
      <p style={{ margin:'0 0 24px', color:'#B4BCC8', fontSize:14 }}>Early design system scaffold.</p>
      <ErrorBoundary fallback={<div style={{ padding:20, background:'#1E2430', border:'1px solid #2A303B', borderRadius:8 }}><h3 style={{ marginTop:0 }}>Section failed to load</h3><p style={{ fontSize:12 }}>Try again or reload the page.</p><button onClick={()=>window.location.reload()} style={{ fontSize:12, padding:'6px 10px' }}>Reload</button></div>}>
      <div style={{ display:'flex', gap:12, alignItems:'center', marginBottom:16 }}>
        <Badge variant="accent">alpha</Badge>
        <Badge variant="success">stable core</Badge>
        <Badge variant="warn">wip</Badge>
        <Button size="sm" variant="secondary" onClick={()=>setShowModal(true)}>Show Modal</Button>
      </div>
      </ErrorBoundary>
      <Stack horizontal gap={20} align="flex-start" wrap>
        <Stack gap={20} style={{ flex: '2 1 520px', minWidth:340 }}>
          <Card title="Learner Profile" actions={<Button size="sm" variant="ghost" onClick={()=>window.location.reload()}>Refresh</Button>}>
            {profileLoading ? <Stack gap={8}><Skeleton height={16}/><Skeleton height={16} width="80%"/><Skeleton height={16} width="60%"/></Stack> : (profile ? <JSONViewer value={profile}/> : <p style={{fontSize:12, opacity:.6}}>No profile.</p>)}
          </Card>
          <Card title="Session" footer={user ? `Role: ${user.role}` : 'Unauthenticated (visit /login)'}>
            {user ? <p style={{fontSize:12, margin:0}}>User: {user.name}</p> : <p style={{fontSize:12, margin:0}}>No active user</p>}
          </Card>
          <Card title="Generate Lesson" actions={<div style={{ display:'flex', gap:8 }}>
            <label style={{ display:'flex', alignItems:'center', gap:4, fontSize:11 }}>
              <input type="checkbox" checked={streamMode} onChange={()=>setStreamMode(v=>!v)} /> Stream
            </label>
            {!streamMode && <Button size="sm" onClick={generate}>Generate</Button>}
            {streamMode && <Button size="sm" variant="secondary" disabled={streamGen.active} onClick={()=>streamGen.start({ learner_id:'learner_demo', unit_id:'unit_math_1', objectives:['addition basics'] })}>{streamGen.active? 'Streaming...' : 'Start Stream'}</Button>}
            {streamMode && streamGen.active && <Button size="sm" variant="ghost" onClick={streamGen.abort}>Abort</Button>}
          </div>} footer={rateRemaining ? `Rate remaining: ${rateRemaining}` : ''}>
            {/* Phase 10 F: Future streaming placeholder (will replace once backend streams) */}
            {/* <div style={{ fontSize:11, opacity:.6 }}>Streaming mode disabled (stub)</div> */}
            {!streamMode && bundle ? <>
              <JSONViewer value={bundle}/>
              <div style={{ marginTop:12 }}>
                <FeedbackWidget itemId={bundleId} learnerId={'learner_demo'} compact />
              </div>
            </> : null}
            {!streamMode && !bundle && <p style={{fontSize:13,opacity:0.7}}>No bundle yet.</p>}
            {streamMode && (
              <div style={{ fontSize:12, lineHeight:1.4, maxHeight:300, overflowY:'auto', background:'#161A21', border:'1px solid #2A303B', borderRadius:6, padding:10 }}>
                {streamGen.chunks.map((c,i)=>(<p key={i} style={{ margin:'0 0 8px' }}>{c}</p>))}
                {streamGen.active && <p style={{ opacity:.6 }}>…</p>}
                {streamGen.complete && <p style={{ color:'#10B981', margin:0 }}>Complete</p>}
                {streamGen.error && <p style={{ color:'#EF4444', margin:0 }}>Error: {streamGen.error}</p>}
                {!streamGen.active && !streamGen.chunks.length && <p style={{ opacity:.6, margin:0 }}>No stream yet.</p>}
              </div>
            )}
            {lastRequestId && <p style={{fontSize:11, color:'#888'}}>Request ID: {lastRequestId}</p>}
          </Card>
        </Stack>
        <Stack gap={20} style={{ flex:'1 1 360px', minWidth:320 }}>
          <Card title="Analytics" actions={<Button size="sm" variant="secondary" onClick={fetchProgress}>Fetch</Button>}>
            {progressLoading ? <Stack gap={6}><Skeleton height={14}/><Skeleton height={14} width="70%"/><Skeleton height={14} width="50%"/></Stack> : (progress ? <JSONViewer value={progress} maxHeight={200}/> : <p style={{fontSize:12,opacity:.6}}>No analytics.</p>)}
          </Card>
          <Card title="Recommended Next" actions={<Button size="sm" variant="secondary" disabled={!user || recsLoading || recsDisabled} onClick={fetchRecs}>{recsLoading ? 'Loading' : 'Refresh'}</Button>} footer={recsVariant ? `Variant: ${recsVariant}` : (recsDisabled ? 'Recommendations disabled' : '')}>
            <div style={{ display:'flex', gap:8, marginBottom:8, alignItems:'center' }}>
              <label style={{ fontSize:11, display:'flex', gap:4, alignItems:'center', cursor:'pointer' }}>
                <input type="checkbox" checked={recsDisabled} onChange={toggleRecs} />
                Disable
              </label>
            </div>
            {!user && <p style={{fontSize:12,opacity:.6}}>Login to see recommendations.</p>}
            {user && recsDisabled && <p style={{fontSize:12,opacity:.6}}>Disabled.</p>}
            {user && !recsDisabled && !recsPanel && <p style={{fontSize:12,opacity:.6}}>Loading…</p>}
            {user && !recsDisabled && recsPanel && recsPanel.length>0 && (
              <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
                {recsPanel.map((r:any)=> (
                  <button key={r.id} onClick={()=>emitTelemetry({ type:'rec.click', data:{ id: r.id, rank: r.rank, variant: recsVariant } })} style={{ textAlign:'left', fontSize:12, padding:'6px 8px', background:'#161A21', border:'1px solid #2A303B', borderRadius:6, cursor:'pointer' }}>
                    <strong>{r.id}</strong> <span style={{opacity:.7}}>score {r.score.toFixed(3)}</span>
                    {r.reason?.length>0 && <em style={{ fontSize:11, opacity:.6 }}> {r.reason.slice(0,3).join(', ')}</em>}
                  </button>
                ))}
              </div>
            )}
          </Card>
          <Card title="Live Recommendations" actions={<Button size="sm" disabled={!!sessionId} onClick={startSession}>{sessionId ? 'Streaming' : 'Start'}</Button>} footer={lastFreshTs ? `Last fresh: ${Math.floor((Date.now()-lastFreshTs)/1000)}s ago` : ''}>
            {sessionId && <p style={{fontSize:12, margin:'4px 0'}}>Session: {sessionId}</p>}
            <div aria-live="polite" aria-relevant="additions" style={{maxHeight:220, overflowY:'auto', display:'flex', flexDirection:'column', gap:6}}>
              {recs.map((r,i)=>(
                <div key={i} style={{ fontSize:12, padding:'6px 8px', background:'#161A21', border:'1px solid #2A303B', borderRadius:6 }}>
                  {r.cached && <strong style={{color:'#10B981'}}>cached </strong>}
                  {r.strategy && !r.cached && <strong style={{color: r.strategy==='explore' ? '#F59E0B':'#6366F1'}}>{r.strategy} </strong>}
                  <code style={{ fontSize:11 }}>{JSON.stringify(r)}</code>
                </div>
              ))}
              {!recs.length && <p style={{fontSize:12, opacity:0.6}}>No events yet.</p>}
            </div>
          </Card>
          <Card title="System" compact>
            <p style={{margin:0,fontSize:12}}>Global RL Remaining: {globalRateRemaining || '—'}</p>
          </Card>
        </Stack>
      </Stack>
      <Modal open={showModal} onClose={()=>setShowModal(false)} title="Phase 2 Components">
        <p style={{ margin:'0 0 12px' }}>Basic Modal & Badge primitives have been added. This dialog demonstrates focus trap, escape & backdrop click close.</p>
        <p style={{ margin:0, fontSize:12, opacity:.7 }}>Enhancements pending: aria-describedby linking, initial focus to first interactive element, and portal optimization.</p>
      </Modal>
  </div>
  </AppShell>
  );
}

export default function Home(){
  const mounted = useHasMounted();
  if(!mounted){
    return <div style={{padding:40,fontSize:12,opacity:.6}}>Loading…</div>;
  }
  return <HomeInner />;
}
