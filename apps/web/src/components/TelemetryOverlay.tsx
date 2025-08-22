import React from 'react';
import { onTelemetry, telemetryStats } from '../lib/telemetry';

export const TelemetryOverlay: React.FC = () => {
  const [vitals, setVitals] = React.useState<any[]>([]);
  const [stats, setStats] = React.useState(telemetryStats());
  React.useEffect(()=>{
    const off = onTelemetry(e => {
      if(e.type === 'web_vital'){
        setVitals(v => [e, ...v].slice(0,10));
      }
      setStats(telemetryStats());
    });
    const id = setInterval(()=> setStats(telemetryStats()), 2000);
    return ()=>{ off(); clearInterval(id); };
  },[]);
  return (
    <div style={{ position:'fixed', bottom:8, left:8, background:'rgba(0,0,0,0.6)', padding:'8px 10px', fontSize:11, fontFamily:'monospace', zIndex:2000, border:'1px solid #333', borderRadius:6, maxWidth:260 }}>
      <strong style={{ fontSize:11 }}>Telemetry</strong> q:{stats.queued} r:{stats.retry} d:{stats.dropped}
      <div style={{ marginTop:6, display:'flex', flexDirection:'column', gap:2 }}>
        {vitals.map(v => (
          <div key={v.ts + v.data?.name} style={{ display:'flex', justifyContent:'space-between' }}>
            <span>{v.data?.name}</span>
            <span style={{ opacity:.8 }}>{Number(v.data?.value).toFixed(1)}</span>
          </div>
        ))}
        {!vitals.length && <em style={{ opacity:.5 }}>no vitals yet</em>}
      </div>
    </div>
  );
};
