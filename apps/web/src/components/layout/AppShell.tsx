import React from 'react';
import Link from 'next/link';
import { colors } from '../../design/tokens';
import { useAuth } from '../../auth/AuthContext';
import { useOnlineStatus } from '../../hooks/useOnlineStatus';

interface NavItem { label: string; href: string }
export const AppShell: React.FC<React.PropsWithChildren<{ title?: string; right?: React.ReactNode; nav?: NavItem[] }>> = ({ title, right, nav, children }) => {
  const pathname = typeof window !== 'undefined' ? window.location.pathname : '';
  const { user } = useAuth();
  const online = useOnlineStatus();
  const effectiveNav = React.useMemo(()=>{
    if(!nav) return nav;
    return nav.filter(item => item.label !== 'Telemetry' || user?.role === 'instructor');
  },[nav, user]);
  return (
    <div style={{ minHeight:'100vh', display:'flex', flexDirection:'column' }}>
      <header style={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:16, padding:'12px 24px', borderBottom:`1px solid ${colors.border}`, background:colors.bgElevated, position:'sticky', top:0, zIndex:10 }}>
        <div style={{ display:'flex', alignItems:'center', gap:24 }}>
          <h1 style={{ margin:0, fontSize:18 }}>{title || 'Adaptive Platform'}</h1>
      {effectiveNav && (
            <nav aria-label="Primary" style={{ display:'flex', alignItems:'center', gap:12 }}>
        {effectiveNav.map(item => {
                const active = pathname === item.href;
                return (
                  <Link key={item.href} href={item.href} style={{ textDecoration:'none', fontSize:14, padding:'4px 8px', borderRadius:6, background: active ? colors.bgAlt : 'transparent', color: active ? colors.text : colors.textDim, border:`1px solid ${active ? colors.border : 'transparent'}` }}>
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          )}
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:12 }}>{right}</div>
      </header>
  {!online && <div role="status" aria-live="polite" style={{ background:'#7C2D12', color:'#FDE68A', padding:'6px 16px', fontSize:12, textAlign:'center' }}>Offline – changes will be saved locally and synced when back online.</div>}
  <main style={{ flex:1, width:'100%', boxSizing:'border-box' }}>{children}</main>
      <footer style={{ padding:'8px 24px', fontSize:12, color:colors.textDim, borderTop:`1px solid ${colors.border}`, background:colors.bgAlt }}>© {new Date().getFullYear()} Adaptive Multimodal Education (dev)</footer>
    </div>
  );
};
