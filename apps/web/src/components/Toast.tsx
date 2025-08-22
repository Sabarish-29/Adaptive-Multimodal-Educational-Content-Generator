import React, { createContext, useCallback, useContext, useState, useEffect } from 'react';
import { colors } from '../design/tokens';

interface Toast { id: string; message: string; type?: 'info'|'error'|'success'|'warn'; ttl?: number; focus?: boolean }
interface ToastContextValue { push: (t: Omit<Toast,'id'>) => void }

const ToastContext = createContext<ToastContextValue | null>(null);

export const ToastProvider: React.FC<React.PropsWithChildren<{}>> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((t: Omit<Toast,'id'>) => {
    const id = crypto.randomUUID();
    setToasts(prev => {
      const next = [...prev, { id, ...t }];
      // Limit stack size
      return next.slice(-5);
    });
    if(t.ttl !== 0){
      const ttl = t.ttl ?? 5000;
      setTimeout(()=>{ setToasts(p => p.filter(x=>x.id!==id)); }, ttl);
    }
    if(t.focus){
      // focus newest toast dismiss button on next frame
      requestAnimationFrame(()=>{
        const el = document.querySelector(`[data-toast-id="${id}"] button` ) as HTMLButtonElement | null;
        el?.focus();
      });
    }
  },[]);

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div aria-live="polite" aria-atomic="true" style={{ position:'fixed', bottom:16, right:16, display:'flex', flexDirection:'column', gap:8, zIndex:1000, maxWidth:360 }}>
  {toasts.map(t => <ToastItem key={t.id} toast={t} onClose={()=>setToasts(p=>p.filter(x=>x.id!==t.id))} />)}
      </div>
    </ToastContext.Provider>
  );
};

export function useToast(){
  const ctx = useContext(ToastContext);
  if(!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

const tone: Record<string,string> = {
  info: colors.bgElevated,
  success: '#064e3b',
  error: '#7f1d1d',
  warn: '#78350f'
};

const border: Record<string,string> = {
  info: colors.border,
  success: '#065f46',
  error: '#991b1b',
  warn: '#92400e'
};

const ToastItem: React.FC<{ toast: Toast; onClose(): void }> = ({ toast, onClose }) => {
  return (
  <div data-toast-id={toast.id} role="status" style={{ background:tone[toast.type||'info'], border:`1px solid ${border[toast.type||'info']}`, padding:'8px 12px', borderRadius:8, boxShadow:'0 2px 6px rgba(0,0,0,0.4)', color:colors.text, fontSize:13, display:'flex', gap:12, alignItems:'flex-start' }}>
      <div style={{ flex:1 }}>{toast.message}</div>
      <button aria-label="Dismiss" onClick={onClose} style={{ background:'transparent', border:'none', color:colors.textDim, cursor:'pointer', fontSize:16, lineHeight:1 }}>×</button>
    </div>
  );
};
