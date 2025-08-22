import React from 'react';
import { AppShell } from '../components/layout/AppShell';
import { useAnalyticsProgress } from '../hooks/data/useAnalyticsProgress';
import { useAuth } from '../auth/AuthContext';
import { useAuthHeaders } from '../auth/useAuthHeaders';
import ReactLazy from 'react';
const LineChart = React.lazy(()=>import('../components/charts/LineChart').then(m=>({ default: m.LineChart })));
const Spark = React.lazy(()=>import('../components/charts/Spark').then(m=>({ default: m.Spark })));
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { JSONViewer } from '../components/JSONViewer';
import { Stack } from '../components/Stack';
import { RouteGuard } from '../components/RouteGuard';

function Page(){
  const { user, switchRole } = useAuth();
  const headers = useAuthHeaders();
  const { data, isLoading, refetch } = useAnalyticsProgress('learner_demo', headers);
  const history = (data?.mastery_history && data.mastery_history.length) ? data.mastery_history : Array.from({length:16}, (_,i)=>({ score: Math.round(50 + Math.sin(i/2)*30 + i ) }));
  return (
  <AppShell title="Analytics" nav={[{label:'Home', href:'/'},{label:'Analytics', href:'/analytics'},{label:'Content', href:'/content'},{label:'Sessions', href:'/sessions'},{label:'Telemetry', href:'/telemetry'}]}>
      <div style={{ maxWidth:900, margin:'0 auto', padding:32 }}>
        <h2 style={{ margin:'0 0 12px' }}>Analytics</h2>
        <p style={{ margin:'0 0 24px', fontSize:14, opacity:.8 }}>Learner progress & mastery snapshots.</p>
        <Stack gap={20}>
          <Card title="Session" footer={user ? `Role: ${user.role}` : 'Not logged in'} actions={user && <Button size="sm" variant="secondary" onClick={()=>switchRole(user.role==='learner'?'instructor':'learner')}>Switch Role</Button>}>
            {user ? <p style={{fontSize:12, margin:0}}>User: {user.name}</p> : <p style={{fontSize:12, margin:0}}>Login required (go to /login)</p>}
          </Card>
          <Card title="Progress" actions={<Button size="sm" onClick={()=>refetch()}>Refresh</Button>}>
            {isLoading ? <p style={{fontSize:12,opacity:.7}}>Loading...</p> : !data ? <p style={{fontSize:12,opacity:.6}}>No data.</p> : (
              <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
                <JSONViewer value={data} maxHeight={220} />
                <div style={{ display:'flex', gap:24, flexWrap:'wrap' }}>
                  <div>
                    <h4 style={{ margin:'0 0 8px', fontSize:12, textTransform:'uppercase', letterSpacing:.5, opacity:.7 }}>Mastery Trend</h4>
                    <React.Suspense fallback={<p style={{fontSize:12,opacity:.6}}>Loading chart…</p>}>
                      <LineChart data={history.map((m:any,i:number)=>({ x:i, y:m.score||0 }))} />
                    </React.Suspense>
                  </div>
                  <div>
                    <h4 style={{ margin:'0 0 8px', fontSize:12, textTransform:'uppercase', letterSpacing:.5, opacity:.7 }}>Recent Scores</h4>
                    <React.Suspense fallback={<p style={{fontSize:12,opacity:.6}}>Loading spark…</p>}>
                      <Spark values={history.slice(-12).map((m:any)=>m.score||0)} />
                    </React.Suspense>
                  </div>
                </div>
              </div>
            )}
          </Card>
        </Stack>
      </div>
    </AppShell>
  );
}

export default function AnalyticsPage(){
  return <RouteGuard><Page/></RouteGuard>;
}
