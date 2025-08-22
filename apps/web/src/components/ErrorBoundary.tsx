import React from 'react';
import { colors } from '../design/tokens';
import { emitTelemetry } from '../lib/telemetry';

interface Props { fallback?: React.ReactNode }
interface State { error: Error | null }

export class ErrorBoundary extends React.Component<React.PropsWithChildren<Props>, State> {
  state: State = { error: null };
  static getDerivedStateFromError(error: Error): State { return { error }; }
  componentDidCatch(error: Error, info: any){
    console.error('Boundary caught error', error, info);
    emitTelemetry({ type:'ui.error', data:{ message: error.message.slice(0,200), stack: (error.stack||'').slice(0,300) } });
  }
  reset = () => { this.setState({ error: null }); };
  render(){
    if(this.state.error){
      return this.props.fallback || (
        <div style={{ padding:32 }}>
          <h2 style={{ marginTop:0 }}>Something went wrong.</h2>
          <pre style={{ background:colors.bgElevated, padding:12, border:`1px solid ${colors.border}`, borderRadius:8, fontSize:12, maxWidth:600, overflow:'auto' }}>{String(this.state.error.message)}</pre>
          <button onClick={this.reset} style={{ marginTop:16 }}>Retry</button>
        </div>
      );
    }
    return this.props.children;
  }
}
