import React from 'react';

export const Stack: React.FC<React.PropsWithChildren<{ gap?: number | string; horizontal?: boolean; align?: string; justify?: string; wrap?: boolean; style?: React.CSSProperties; }>> = ({ gap = 16, horizontal, align='stretch', justify='flex-start', wrap=false, style, children }) => {
  return (
    <div style={{ display:'flex', flexDirection: horizontal ? 'row':'column', gap, alignItems: align as any, justifyContent: justify as any, flexWrap: wrap ? 'wrap':'nowrap', ...style }}>{children}</div>
  );
};

// Simple horizontal/vertical spacing utilities could be added here later.
