import React from 'react';
import { radii, shadows } from '../design/tokens';

export const Card: React.FC<React.PropsWithChildren<{ title?: string; actions?: React.ReactNode; compact?: boolean; footer?: React.ReactNode; }>> = ({ title, actions, children, compact, footer }) => {
  return (
    <section
      aria-label={title}
      style={{
  background: 'var(--c-bg-elevated)',
  border: '1px solid var(--c-border)',
        borderRadius: radii.lg,
        padding: compact ? '12px 14px' : '18px 20px',
        boxShadow: shadows.sm,
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        minWidth: 0
      }}
    >
      {(title || actions) && (
        <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          {title && <h3 style={{ margin: 0, fontSize: 16 }}>{title}</h3>}
          {actions && <div>{actions}</div>}
        </header>
      )}
      <div style={{ fontSize: 14, lineHeight: 1.5, minWidth: 0 }}>{children}</div>
  {footer && <footer style={{ fontSize: 12, color: 'var(--c-text-dim)' }}>{footer}</footer>}
    </section>
  );
};
