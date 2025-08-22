import React, { useState } from 'react';
import { colors, radii, font } from '../design/tokens';

export const JSONViewer: React.FC<{ value: any; maxHeight?: number }> = ({ value, maxHeight=260 }) => {
  const [expanded, setExpanded] = useState(true);
  return (
    <div style={{ border:`1px solid ${colors.border}`, borderRadius:radii.md, background:'#11161d', fontFamily: font.mono, fontSize:12, display:'flex', flexDirection:'column' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'4px 8px', cursor:'pointer', userSelect:'none' }} onClick={()=>setExpanded(e=>!e)}>
        <span style={{ color: colors.textDim }}>{expanded ? '▼' : '▶'} JSON</span>
        <span style={{ color: colors.textDim }}>{expanded ? 'collapse':'expand'}</span>
      </div>
      {expanded && (
        <pre style={{ margin:0, padding:'8px 10px', overflow:'auto', maxHeight }}>{JSON.stringify(value, null, 2)}</pre>
      )}
    </div>
  );
};
