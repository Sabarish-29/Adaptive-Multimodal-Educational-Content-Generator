import React from 'react';
import { colors, radii, font, transitions } from '../design/tokens';

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
};

const VARIANT: Record<string, { bg: string; color: string; hover: string; border?: string }> = {
  primary: { bg: 'var(--c-accent)', color: 'var(--c-text)', hover: 'var(--c-accent-hover)' },
  secondary: { bg: 'var(--c-bg-alt)', color: 'var(--c-text)', hover: 'rgba(0,0,0,0.08)', border: 'var(--c-border)' },
  ghost: { bg: 'transparent', color: 'var(--c-text-dim)', hover: 'var(--c-bg-alt)' },
  danger: { bg: 'var(--c-danger)', color: '#fff', hover: '#f87171' }
};

const PAD: Record<string, string> = { sm: '4px 10px', md: '8px 16px', lg: '12px 22px' };
const FS: Record<string, string> = { sm: font.size.sm, md: font.size.md, lg: font.size.lg };

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled,
  loading,
  iconLeft,
  iconRight,
  children,
  style,
  ...rest
}) => {
  const v = VARIANT[variant];
  return (
    <button
      disabled={disabled || loading}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: PAD[size],
        fontSize: FS[size],
        lineHeight: 1.2,
        fontWeight: 500,
        borderRadius: radii.md,
        border: v.border ? `1px solid ${v.border}` : '1px solid transparent',
        background: v.bg,
        color: v.color,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.55 : 1,
        transition: `background ${transitions.fast}, box-shadow ${transitions.fast}`,
        ...style
      }}
      onMouseEnter={e => { if (!disabled && !loading) (e.currentTarget.style.background = v.hover); }}
      onMouseLeave={e => { if (!disabled && !loading) (e.currentTarget.style.background = v.bg); }}
      {...rest}
    >
      {iconLeft && <span style={{ display: 'inline-flex' }}>{iconLeft}</span>}
      <span>{loading ? '…' : children}</span>
      {iconRight && <span style={{ display: 'inline-flex' }}>{iconRight}</span>}
    </button>
  );
};
