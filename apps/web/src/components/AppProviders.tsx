import React from 'react';
import { ThemeProvider } from '../theme/ThemeContext';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '../hooks/data/queryClient';
import { ToastProvider, useToast } from './Toast';
import { ErrorBoundary } from './ErrorBoundary';
import { onTelemetry } from '../lib/telemetry';

function QueryEventsListener(){
  const { push } = useToast();
  React.useEffect(()=>{
    const onError = (e: any) => {
      const err = e.detail?.error || e.detail;
      const msg = err?.message || 'Request failed';
      push({ message: msg, type:'error', focus:true });
    };
    const onSuccess = (e: any) => {
      const metaMsg = e.detail?.message;
      const msg = metaMsg || 'Operation succeeded';
      push({ message: msg, type:'success' });
    };
    window.addEventListener('rq:error', onError as any);
    window.addEventListener('rq:success', onSuccess as any);
    return ()=>{ window.removeEventListener('rq:error', onError as any); window.removeEventListener('rq:success', onSuccess as any); };
  },[push]);
  return null;
}

function TelemetryConsole(){
  React.useEffect(()=>{
    if(process.env.NODE_ENV === 'production') return;
    const off = onTelemetry(e => {
      // eslint-disable-next-line no-console
      console.debug('[telemetry]', e.type, e.durMs!=null? `${e.durMs.toFixed(1)}ms`:'', e.data||'');
    });
    return () => { off(); };
  },[]);
  return null;
}

// Global error piping via queryClient default options
// Add lightweight wrappers via setQueryDefaults & setMutationDefaults for a wildcard key
// (React Query requires a specific key, so we hook into global event of cache subscribe instead)
queryClient.getQueryCache().subscribe(event => {
  // event has { type, query } shape; inspect query state for failure
  const anyEvent: any = event;
  const q = anyEvent?.query;
  if(q && q.state?.status === 'error' && q.state.error){
    if(typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('rq:error', { detail: { error: q.state.error } }));
  }
});
queryClient.getMutationCache().subscribe(event => {
  const anyEvent: any = event;
  const m = anyEvent?.mutation;
  if(m && m.state?.status === 'error' && m.state.error){
    if(typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('rq:error', { detail: { error: m.state.error } }));
  } else if (m && m.state?.status === 'success' && m.state.data){
    const message = m.options?.meta?.successMessage;
    if(typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('rq:success', { detail: { message } }));
  }
});

export const AppProviders: React.FC<React.PropsWithChildren<{}>> = ({ children }) => (
  <ThemeProvider>
    <ToastProvider>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <QueryEventsListener />
          <TelemetryConsole />
          {children}
        </QueryClientProvider>
      </ErrorBoundary>
    </ToastProvider>
  </ThemeProvider>
);
