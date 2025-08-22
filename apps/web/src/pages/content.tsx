import React from 'react';
import { AppShell } from '../components/layout/AppShell';
import { useGenerateLesson } from '../hooks/data/useGenerateLesson';
import { useAuth } from '../auth/AuthContext';
import { RouteGuard } from '../components/RouteGuard';
import { useAuthHeaders } from '../auth/useAuthHeaders';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { JSONViewer } from '../components/JSONViewer';
import { Stack } from '../components/Stack';
import { FeedbackWidget } from '../components/FeedbackWidget';

function Page(){
  const headers = useAuthHeaders();
  const { user } = useAuth();
  const [bundle, setBundle] = React.useState<any>(null);
  const [lastRequestId, setLastRequestId] = React.useState('');
  const [rateRemaining, setRateRemaining] = React.useState('');
  const mutation = useGenerateLesson(headers);
  const generate = async () => {
    const { data, headers: h } = await mutation.mutateAsync({ learner_id: 'learner_demo', unit_id: 'unit_math_1', objectives: ['addition basics'] });
    setBundle(data); setLastRequestId(h['x-request-id'] || ''); const rl = h['x-ratelimit-remaining']; if(rl) setRateRemaining(rl as string);
  };
  const bundleId = bundle?.bundle_id || bundle?.id || 'latest_bundle';
  return (
  <AppShell title="Content" nav={[{label:'Home', href:'/'},{label:'Analytics', href:'/analytics'},{label:'Content', href:'/content'},{label:'Sessions', href:'/sessions'},{label:'Telemetry', href:'/telemetry'}]}>
      <div style={{ maxWidth:900, margin:'0 auto', padding:32 }}>
        <h2 style={{ margin:'0 0 12px' }}>Content Generation</h2>
        <p style={{ margin:'0 0 24px', fontSize:14, opacity:.8 }}>Generate lesson bundles for a learner & unit.</p>
        <Stack gap={20}>
          <Card title="Session" footer={user ? `Role: ${user.role}` : 'Not logged in (visit /login)'}>
            {user ? <p style={{fontSize:12, margin:0}}>User: {user.name}</p> : <p style={{fontSize:12, margin:0}}>No active session</p>}
          </Card>
          <Card title="Generate Lesson" actions={<Button size="sm" onClick={generate} disabled={mutation.isPending || !user}>{mutation.isPending ? 'Generating...' : 'Generate'}</Button>} footer={rateRemaining?`Rate remaining: ${rateRemaining}`:''}>
            {bundle ? <>
              <JSONViewer value={bundle} maxHeight={300}/>
              <div style={{ marginTop:12 }}>
                <FeedbackWidget itemId={bundleId} learnerId={'learner_demo'} />
              </div>
            </> : <p style={{fontSize:12, opacity:.6}}>No bundle yet.</p>}
            {lastRequestId && <p style={{fontSize:11}}>Request ID: {lastRequestId}</p>}
          </Card>
        </Stack>
      </div>
    </AppShell>
  );
}

export default function ContentPage(){
  return <RouteGuard><Page/></RouteGuard>;
}
