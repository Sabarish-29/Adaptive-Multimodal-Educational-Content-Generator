import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({ label, helperText, error, id, style, ...rest }) => {
  // Always call hook unconditionally for lint rule; prefer passed id when provided.
  const autoId = React.useId();
  const inputId = id ?? autoId;
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:4 }}>
      {label && <label htmlFor={inputId} style={{ fontSize:12, fontWeight:500, letterSpacing:'.5px' }}>{label}</label>}
      <input
        id={inputId}
        style={{
          padding:'8px 10px',
          border:'1px solid var(--c-border)',
          borderRadius:6,
          background:'var(--c-bg-alt)',
          color:'var(--c-text)',
          fontSize:14,
          outline:'none',
          transition:'border .15s',
          ...style
        }}
        {...rest}
      />
      {(helperText || error) && (
        <div style={{ fontSize:11, color: error ? 'var(--c-danger)' : 'var(--c-text-dim)' }}>{error || helperText}</div>
      )}
    </div>
  );
};
