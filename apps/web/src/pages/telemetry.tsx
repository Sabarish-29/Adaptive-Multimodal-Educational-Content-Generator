import React from 'react';
import { AppShell } from '../components/layout/AppShell';
import { RouteGuard } from '../components/RouteGuard';
import { Card } from '../components/Card';
import { Stack } from '../components/Stack';
import { LineChart } from '../components/charts/LineChart';
import { Spark } from '../components/charts/Spark';
import { Button } from '../components/Button';
import { services } from '../lib/api';

interface TelemetryRow { type: string; count: number; avgDur?: number; maxDur?: number; p95Dur?: number }

export default function TelemetryPage(){
  return <RouteGuard roles={['instructor']}><Inner/></RouteGuard>;
}

function Inner(){
  const [stats, setStats] = React.useState<TelemetryRow[]>([]);
  const [alerts, setAlerts] = React.useState<any[]>([]);
  const [rollups, setRollups] = React.useState<any[]>([]);
  const [events, setEvents] = React.useState<any[]>([]);
  const [recMetrics, setRecMetrics] = React.useState<any|null>(null);
  const [loading, setLoading] = React.useState(false);
  const load = async ()=>{
    setLoading(true);
    try {
      const s = await fetch(`${services.analytics}/v1/telemetry/stats`).then(r=>r.json());
      setStats(s.types||[]);
      setAlerts(s.alerts||[]);
      const l = await fetch(`${services.analytics}/v1/telemetry/latest?limit=50`).then(r=>r.json());
      setEvents(l.events||[]);
  const ru = await fetch(`${services.analytics}/v1/telemetry/rollups/hourly?hours=24`).then(r=>r.json());
      setRollups(ru.rollups||[]);
  const rm = await fetch(`${services.analytics}/v1/recommendations/metrics`).then(r=>r.json());
  setRecMetrics(rm);
    } finally { setLoading(false); }
  };
  React.useEffect(()=>{ load(); const id = setInterval(load, 15000); return ()=>clearInterval(id); },[]);
  return (
    <AppShell title="Telemetry" nav={[{label:'Home', href:'/'},{label:'Analytics', href:'/analytics'},{label:'Telemetry', href:'/telemetry'}] }>
      <div style={{ maxWidth:1240, margin:'0 auto', padding:32 }}>
        <h2 style={{ margin:'0 0 12px' }}>Telemetry Dashboard</h2>
        <p style={{ margin:'0 0 24px', fontSize:14, opacity:.8 }}>Performance & event statistics (auto-refresh 15s).</p>
        <Button size="sm" variant="secondary" onClick={load} disabled={loading}>{loading? 'Refreshing...' : 'Refresh'}</Button>
        <Stack gap={24} style={{ marginTop:24 }}>
          <Card title="Alerts">
            <p style={{ margin:'0 0 12px', fontSize:11, opacity:.6 }}>Active threshold breaches (p95 latency)</p>
            {!alerts.length && <p style={{fontSize:12,opacity:.6}}>No active alerts.</p>}
            <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
              {alerts.map(a => (
                <div key={a.type+a.metric} style={{ fontSize:11, padding:'6px 8px', background:'#361d1d', border:'1px solid #5b2c2c', borderRadius:6 }}>
                  <strong>{a.type}</strong> {a.metric} {a.value?.toFixed?.(1)}ms {'>'}= {a.threshold}ms
                </div>
              ))}
            </div>
          </Card>
          <Card title="Event Types">
            <p style={{ margin:'0 0 12px', fontSize:11, opacity:.6 }}>Counts & latency (avg/p95/max)</p>
            {!stats.length && <p style={{fontSize:12,opacity:.6}}>No data.</p>}
            <div style={{ display:'flex', flexWrap:'wrap', gap:24 }}>
              {stats.map(s => (
                <div key={s.type} style={{ minWidth:220 }}>
                  <h4 style={{ margin:'0 0 4px', fontSize:12, letterSpacing:.5, textTransform:'uppercase', opacity:.7 }}>{s.type}</h4>
                  <p style={{ margin:0, fontSize:11, opacity:.7 }}>count {s.count}</p>
                  {(s.avgDur!=null) && <p style={{ margin:'4px 0 0', fontSize:11 }}>avg {s.avgDur.toFixed(1)}ms p95 {s.p95Dur?.toFixed?.(1)||'—'} max {s.maxDur?.toFixed?.(1)||'—'}</p>}
                </div>
              ))}
            </div>
          </Card>
          <Card title="Recommendations Metrics">
            <p style={{ margin:'0 0 12px', fontSize:11, opacity:.6 }}>CTR & acceptance (last {recMetrics?.windowMinutes||'—'}m)</p>
            {!recMetrics && <p style={{fontSize:12,opacity:.6}}>Loading…</p>}
            {recMetrics && (
              <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
                <div style={{ fontSize:11, background:'#161A21', border:'1px solid #2A303B', borderRadius:6, padding:'6px 8px' }}>
                  <strong>Overall</strong> fetches {recMetrics.overall.fetches} clicks {recMetrics.overall.clicks} ctr {(recMetrics.overall.ctr*100).toFixed(1)}% acceptance {(recMetrics.overall.acceptance*100).toFixed(1)}%
                </div>
                <div style={{ display:'flex', flexWrap:'wrap', gap:12 }}>
                  {recMetrics.variants.map((v:any)=>(
                    <div key={v.variant} style={{ fontSize:11, background:'#161A21', border:'1px solid #2A303B', borderRadius:6, padding:'6px 8px', minWidth:160 }}>
                      <strong>{v.variant}</strong><br/>
                      f {v.fetches} c {v.clicks} ctr {(v.ctr*100).toFixed(1)}% acc {(v.acceptance*100).toFixed(1)}%
                    </div>
                  ))}
                  {!recMetrics.variants.length && <p style={{fontSize:12,opacity:.6}}>No variant data.</p>}
                </div>
              </div>
            )}
          </Card>
          <Card title="Latency (ms)">
            <p style={{ margin:'0 0 12px', fontSize:11, opacity:.6 }}>Relative view of p95 per type (spark series)</p>
            <div style={{ display:'flex', gap:32, flexWrap:'wrap' }}>
              {stats.filter(s=>s.p95Dur!=null).map(s => (
                <div key={s.type} style={{ width:160 }}>
                  <h5 style={{ margin:'0 0 4px', fontSize:11 }}>{s.type}</h5>
                  <Spark values={[s.avgDur||0, s.p95Dur||0, s.maxDur||0]} />
                </div>
              ))}
              {!stats.filter(s=>s.p95Dur!=null).length && <p style={{fontSize:12,opacity:.6}}>No latency metrics yet.</p>}
            </div>
          </Card>
          <Card title="Hourly Rollups (last 24h)">
            <p style={{ margin:'0 0 12px', fontSize:11, opacity:.6 }}>Per-hour counts (most recent first)</p>
            {!rollups.length && <p style={{fontSize:12,opacity:.6}}>No rollups yet.</p>}
            <div style={{ overflowX:'auto' }}>
              <table style={{ borderCollapse:'collapse', fontSize:11 }}>
                <thead>
                  <tr>
                    <th style={{ textAlign:'left', padding:'4px 8px', borderBottom:'1px solid #2A303B' }}>Hour (UTC)</th>
                    {Array.from(new Set(rollups.flatMap(r=>Object.keys(r.types||{})))).map(t => (
                      <th key={t} style={{ textAlign:'right', padding:'4px 8px', borderBottom:'1px solid #2A303B' }}>{t}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rollups.slice(0,24).map(r => {
                    const date = new Date(r.hourStart);
                    const label = date.toISOString().slice(11,16);
                    const allTypes = Array.from(new Set(rollups.flatMap(rr=>Object.keys(rr.types||{}))));
                    return (
                      <tr key={r.hourStart}>
                        <td style={{ padding:'4px 8px', borderBottom:'1px solid #1e242d' }}>{label}</td>
                        {allTypes.map(t => (
                          <td key={t} style={{ padding:'4px 8px', textAlign:'right', borderBottom:'1px solid #1e242d', opacity: r.types[t]?1:.25 }}>{r.types[t]?.count ?? '—'}</td>
                        ))}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
          <Card title="Recent Events">
            <p style={{ margin:'0 0 12px', fontSize:11, opacity:.6 }}>Last 50 raw events (most recent first)</p>
            <div style={{ maxHeight:320, overflowY:'auto', display:'flex', flexDirection:'column', gap:6 }}>
              {events.map(e => (
                <div key={e._id} style={{ fontSize:11, background:'#161A21', border:'1px solid #2A303B', borderRadius:6, padding:'6px 8px' }}>
                  <strong>{e.type}</strong> {e.durMs!=null && <span style={{opacity:.7}}>{e.durMs.toFixed(1)}ms </span>}
                  <code style={{ fontSize:10 }}>{JSON.stringify(e.data||{})}</code>
                </div>
              ))}
              {!events.length && <p style={{fontSize:12,opacity:.6}}>No events yet.</p>}
            </div>
          </Card>
        </Stack>
      </div>
    </AppShell>
  );
}
