import React from 'react';
import { AppShell } from '../components/layout/AppShell';
import { useLiveSession } from '../hooks/data/useLiveSession';
import { useAuth } from '../auth/AuthContext';
import { useAuthHeaders } from '../auth/useAuthHeaders';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { Stack } from '../components/Stack';
import { RouteGuard } from '../components/RouteGuard';

function Page(){
  const headers = useAuthHeaders();
  const { user } = useAuth();
  const { start, sessionId, events, lastFreshTs } = useLiveSession(headers, 'learner_demo', 'unit_math_1');
  return (
  <AppShell title="Sessions" nav={[{label:'Home', href:'/'},{label:'Analytics', href:'/analytics'},{label:'Content', href:'/content'},{label:'Sessions', href:'/sessions'},{label:'Telemetry', href:'/telemetry'}]}>
      <div style={{ maxWidth:900, margin:'0 auto', padding:32 }}>
        <h2 style={{ margin:'0 0 12px' }}>Live Session Stream</h2>
        <p style={{ margin:'0 0 24px', fontSize:14, opacity:.8 }}>Start a live recommendation stream and inspect events.</p>
        <Stack gap={20}>
          <Card title="Session" footer={user ? `Role: ${user.role}` : 'Not logged in (visit /login)'}>
            {user ? <p style={{fontSize:12, margin:0}}>User: {user.name}</p> : <p style={{fontSize:12, margin:0}}>No active session</p>}
          </Card>
          <Card title="Live Recommendations" actions={<Button size="sm" disabled={!!sessionId || !user} onClick={()=>start()}>{sessionId ? 'Streaming' : 'Start'}</Button>} footer={lastFreshTs ? `Last fresh: ${Math.floor((Date.now()-lastFreshTs)/1000)}s ago` : ''}>
            {sessionId && <p style={{fontSize:12}}>Session: {sessionId}</p>}
            <div style={{ maxHeight:300, overflow:'auto', display:'flex', flexDirection:'column', gap:6 }}>
              {events.map((e,i)=>(<pre key={i} style={{ margin:0, fontSize:11, background:'#161A21', padding:6, borderRadius:4 }}>{JSON.stringify(e)}</pre>))}
              {!events.length && <p style={{fontSize:12, opacity:.6}}>No events yet.</p>}
            </div>
          </Card>
        </Stack>
      </div>
    </AppShell>
  );
}

export default function SessionsPage(){
  return <RouteGuard><Page/></RouteGuard>;
}
