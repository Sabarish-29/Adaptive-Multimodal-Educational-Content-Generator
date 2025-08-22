import React from 'react';
import { colors, radii, font } from '../design/tokens';

type Tone = 'info' | 'success' | 'warn' | 'error';
const toneMap: Record<Tone, { bg: string; border: string; fg: string }> = {
  info: { bg: colors.bgElevated, border: colors.border, fg: colors.text },
  success: { bg: '#064e3b', border: '#065f46', fg: '#ECFDF5' },
  warn: { bg: '#78350f', border: '#92400e', fg: '#FEF3C7' },
  error: { bg: '#7f1d1d', border: '#991b1b', fg: '#FEE2E2' }
};

interface InlineAlertProps { tone?: Tone; title?: string; onClose?: () => void; children?: React.ReactNode }

export const InlineAlert: React.FC<InlineAlertProps> = ({ tone='info', title, onClose, children }) => {
  const t = toneMap[tone];
  return (
    <div role={tone==='error' ? 'alert' : 'status'} style={{ background:t.bg, border:`1px solid ${t.border}`, color:t.fg, padding:'10px 14px', borderRadius:radii.md, fontSize:font.size.sm, lineHeight:1.4, display:'flex', gap:12 }}>
      <div style={{ flex:1 }}>
        {title && <div style={{ fontWeight:600, marginBottom:4 }}>{title}</div>}
        <div>{children}</div>
      </div>
      {onClose && <button aria-label="Dismiss" onClick={onClose} style={{ background:'transparent', border:'none', color:t.fg, cursor:'pointer', fontSize:16, lineHeight:1 }}>×</button>}
    </div>
  );
};
