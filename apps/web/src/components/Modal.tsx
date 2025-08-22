import React, { useEffect, useRef } from 'react';
import { colors, radii, shadows } from '../design/tokens';

interface ModalProps { open: boolean; onClose(): void; title?: string; maxWidth?: number | string; descriptionId?: string; initialFocusSelector?: string; returnFocusRef?: React.RefObject<HTMLElement> }

export const Modal: React.FC<React.PropsWithChildren<ModalProps>> = ({ open, onClose, title, maxWidth=560, descriptionId, initialFocusSelector, returnFocusRef, children }) => {
  const ref = useRef<HTMLDivElement>(null);
  // Close on escape
  useEffect(()=>{
    if(!open) return;
    const handler = (e: KeyboardEvent) => { if(e.key==='Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return ()=> window.removeEventListener('keydown', handler);
  },[open,onClose]);
  // Focus trap minimal
  useEffect(()=>{
    if(open && ref.current){
      const prev = document.activeElement as HTMLElement | null;
      const toFocus = initialFocusSelector ? ref.current.querySelector<HTMLElement>(initialFocusSelector) : null;
      (toFocus || ref.current).focus();
      return ()=> { (returnFocusRef?.current || prev)?.focus(); };
    }
  },[open, initialFocusSelector, returnFocusRef]);
  // Focus trap: cycle Tab within modal content
  useEffect(()=>{
    if(!open) return;
    function handleKey(e: KeyboardEvent){
      if(e.key !== 'Tab') return;
      const root = ref.current; if(!root) return;
      const focusable = Array.from(root.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
      )).filter(el=>!el.hasAttribute('data-focus-guard'));
      if(!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length -1];
      if(e.shiftKey && document.activeElement === first){ e.preventDefault(); last.focus(); }
      else if(!e.shiftKey && document.activeElement === last){ e.preventDefault(); first.focus(); }
    }
    window.addEventListener('keydown', handleKey, true);
    return ()=> window.removeEventListener('keydown', handleKey, true);
  },[open]);
  // Manage aria-hidden on body children when modal open (simple approach)
  useEffect(()=>{
    if(open){
      const bodyChildren = Array.from(document.body.children).filter(c=>!(c as HTMLElement).hasAttribute('data-backdrop'));
      bodyChildren.forEach(el=> el.setAttribute('aria-hidden','true'));
      return ()=> bodyChildren.forEach(el=> el.removeAttribute('aria-hidden'));
    }
  },[open]);
  if(!open) return null;
  const descId = descriptionId || (title ? 'modal-desc-' + Math.random().toString(36).slice(2) : undefined);
  return (
    <div data-backdrop style={{ position:'fixed', inset:0, background:'rgba(0,0,0,0.55)', backdropFilter:'blur(2px)', display:'flex', alignItems:'flex-start', justifyContent:'center', padding:'10vh 24px', zIndex:1000 }} onMouseDown={(e)=>{ if(e.target===e.currentTarget) onClose(); }}>
      <div ref={ref} role="dialog" aria-modal="true" aria-labelledby={title ? 'modal-title' : undefined} aria-describedby={descId} tabIndex={-1} style={{ outline:'none', background:colors.bgElevated, color:colors.text, border:`1px solid ${colors.border}`, boxShadow:shadows.md, borderRadius:radii.lg, width:'100%', maxWidth, padding:'24px 28px', display:'flex', flexDirection:'column', gap:16 }}>
        {title && <h2 id="modal-title" style={{ margin:'0 0 4px', fontSize:18 }}>{title}</h2>}
        <div id={descId} style={{ fontSize:14, lineHeight:1.5 }}>{children}</div>
        <div style={{ display:'flex', justifyContent:'flex-end', gap:12 }}>
          <button autoFocus onClick={onClose} style={{ background:colors.bgAlt, color:colors.text, border:`1px solid ${colors.border}`, borderRadius:radii.md, padding:'6px 14px', cursor:'pointer' }}>Close</button>
        </div>
      </div>
    </div>
  );
};
