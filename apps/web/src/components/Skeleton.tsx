import React from 'react';

export const Skeleton: React.FC<{ width?: number | string; height?: number | string; radius?: number | string; shimmer?: boolean; }> = ({ width='100%', height=14, radius=4, shimmer=true }) => {
  return (
    <span
      aria-hidden="true"
      style={{
        display:'block',
        background:'linear-gradient(90deg, var(--c-bg-alt) 0%, var(--c-bg-elevated) 50%, var(--c-bg-alt) 100%)',
        backgroundSize: shimmer ? '200% 100%' : undefined,
        animation: shimmer ? 'sk 1.4s ease-in-out infinite' : undefined,
        width,
        height,
        borderRadius: radius,
        opacity:0.7
      }}
    />
  );
};

// Keyframes via style tag (could be moved to global CSS)
if (typeof document !== 'undefined' && !document.getElementById('sk-anim')) {
  const el = document.createElement('style');
  el.id = 'sk-anim';
  el.innerHTML = '@keyframes sk {0% {background-position:0 0;} 100% {background-position:-200% 0;}}';
  document.head.appendChild(el);
}
