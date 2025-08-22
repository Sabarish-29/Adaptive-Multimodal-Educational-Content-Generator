import React from 'react';
import { colors, radii, font } from '../design/tokens';

type Variant = 'neutral' | 'accent' | 'success' | 'warn' | 'danger' | 'outline';
interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> { variant?: Variant; size?: 'sm'|'md'; round?: boolean }

const variantStyles: Record<Variant, React.CSSProperties> = {
  neutral: { background: colors.bgElevated, color: colors.textDim, border: `1px solid ${colors.border}` },
  accent: { background: colors.accent, color: '#fff', border: '1px solid transparent' },
  success: { background: colors.success, color: '#fff', border: '1px solid transparent' },
  warn: { background: colors.warn, color: '#000', border: '1px solid transparent' },
  danger: { background: colors.danger, color: '#fff', border: '1px solid transparent' },
  outline: { background: 'transparent', color: colors.textDim, border: `1px solid ${colors.border}` }
};

export const Badge: React.FC<BadgeProps> = ({ variant='neutral', size='sm', round=false, style, children, ...rest }) => {
  const padding = size === 'sm' ? '2px 6px' : '4px 10px';
  const fontSize = size === 'sm' ? font.size.xs : font.size.sm;
  return (
    <span style={{ display:'inline-flex', alignItems:'center', gap:4, fontSize, lineHeight:1.2, fontWeight:500, padding, borderRadius: round ? radii.pill : radii.md, userSelect:'none', ...variantStyles[variant], ...style }} {...rest}>{children}</span>
  );
};
