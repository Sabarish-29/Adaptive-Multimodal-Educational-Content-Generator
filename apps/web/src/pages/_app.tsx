import type { AppProps } from 'next/app';
import React from 'react';
import Head from 'next/head';
import '../design/GlobalStyles.css';
import { AuthProvider, useAuth } from '../auth/AuthContext';
import { AppProviders } from '../components/AppProviders';
import { configureTelemetry, initWebVitals, emitTelemetry, getAnonId, mark, markEnd, flushPending } from '../lib/telemetry';
import { useRouter } from 'next/router';
import { TelemetryOverlay } from '../components/TelemetryOverlay';

function TelemetryBootstrap(){
  const { user } = useAuth();
  const router = useRouter();
  React.useEffect(()=>{
    const base = process.env.NEXT_PUBLIC_API_GATEWAY ? '/api/analytics' : (process.env.NEXT_PUBLIC_ANALYTICS_URL || 'http://localhost:8005');
    configureTelemetry({ endpoint: base.replace(/\/$/, '') + '/v1/telemetry/events' });
    initWebVitals();
    const rid = crypto.randomUUID();
  emitTelemetry({ type:'page.view', data:{ path: window.location.pathname }, rid, role: user?.role, anonId: getAnonId() });
  },[user]);
  // Flush on route change start, mark navigation
  React.useEffect(()=>{
    const handleStart = (url: string) => { mark('nav'); flushPending(); emitTelemetry({ type:'nav.start', data:{ to: url } }); };
    const handleComplete = (url: string) => { markEnd('nav','nav.dur'); emitTelemetry({ type:'nav.complete', data:{ to: url } }); };
    router.events.on('routeChangeStart', handleStart);
    router.events.on('routeChangeComplete', handleComplete);
    router.events.on('routeChangeError', ()=> emitTelemetry({ type:'nav.error' }));
    return ()=>{
      router.events.off('routeChangeStart', handleStart);
      router.events.off('routeChangeComplete', handleComplete);
      router.events.off('routeChangeError', ()=>{});
    };
  },[router]);
  return null;
}

export default function MyApp({ Component, pageProps }: AppProps){
  // Generate a nonce per render (per request on server, per navigation on client)
  const nonce = React.useMemo(()=>{
    if (typeof window === 'undefined') {
      // Avoid random differing server/client markup; send placeholder stable token
      return 'server-nonce-placeholder';
    }
    let n = (window as any).__cspNonce;
    if(!n){
      if(typeof crypto !== 'undefined' && crypto.randomUUID){
        n = crypto.randomUUID().replace(/-/g,'').slice(0,16);
      } else {
        n = Math.random().toString(36).slice(2,18);
      }
      (window as any).__cspNonce = n;
    }
    return n;
  },[]);
  // Only emit CSP meta in production; skip in dev to avoid interfering with Next.js dev runtime if misconfigured.
  let csp: string | null = null;
  if(process.env.NODE_ENV === 'production'){
    const connectExtra = [process.env.NEXT_PUBLIC_ANALYTICS_URL || 'http://localhost:8004', 'http://localhost:8001', 'http://localhost:8002', 'http://localhost:8003']
      .map(u=>u.replace(/\/$/,'')).join(' ');
    csp = [
      "default-src 'self'",
      "base-uri 'self'",
      "frame-ancestors 'none'",
      "object-src 'none'",
      "img-src 'self' data:",
      `script-src 'self' 'nonce-${nonce}'`,
      `style-src 'self' 'nonce-${nonce}'`,
      `connect-src 'self' ${connectExtra} ws: wss:`,
      "font-src 'self' data:",
      "form-action 'self'"
    ].join('; ');
  }
  return (
    <AuthProvider>
      <AppProviders>
        <Head>
          {csp && <meta httpEquiv="Content-Security-Policy" content={csp} />}
        </Head>
        <TelemetryBootstrap />
        <Component {...pageProps} />
        {process.env.NEXT_PUBLIC_TELEMETRY_OVERLAY === 'true' && <TelemetryOverlay />}
      </AppProviders>
    </AuthProvider>
  );
}
