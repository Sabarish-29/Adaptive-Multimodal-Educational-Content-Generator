import React, { useState, useRef } from 'react';
import { colors, radii, shadows, font } from '../design/tokens';

interface TooltipProps { label: string; delay?: number; children: React.ReactElement }

export const Tooltip: React.FC<TooltipProps> = ({ label, delay=300, children }) => {
  const [open, setOpen] = useState(false);
  const tid = useRef<any>();
  const id = useRef(`tt-${Math.random().toString(36).slice(2)}`);
  const clear = () => { if(tid.current){ clearTimeout(tid.current); tid.current = undefined; } };
  const show = () => { clear(); tid.current = setTimeout(()=>setOpen(true), delay); };
  const hide = () => { clear(); setOpen(false); };
  return (
    <span data-testid="tooltip-wrapper" style={{ position:'relative', display:'inline-flex' }} onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide}>
      {React.cloneElement(children, { 'aria-describedby': id.current })}
      {open && (
        <span role="tooltip" id={id.current} style={{ position:'absolute', bottom:'100%', left:'50%', transform:'translate(-50%, -6px)', background:colors.bgElevated, color:colors.text, padding:'4px 8px', fontSize:font.size.xs, borderRadius:radii.sm, border:`1px solid ${colors.border}`, whiteSpace:'nowrap', boxShadow:shadows.sm, zIndex:10 }}>
          {label}
        </span>
      )}
    </span>
  );
};
