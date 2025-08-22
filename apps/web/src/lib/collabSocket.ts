// Lightweight websocket client for collaborative cursors / presence
// Protocol (JSON line):
// { t: 'hello', id }
// { t: 'cursor', id, line, ch }
// { t: 'presence', id }

export interface CollabCursor { id: string; line: number; ch: number; ts: number }

type Listener = (msg: any) => void;

export class CollabSocket {
  private ws: WebSocket | null = null;
  private listeners = new Set<Listener>();
  private url: string;
  private id: string;
  private retry = 0;

  constructor(url: string, id: string){
    this.url = url;
    this.id = id;
    this.connect();
  }

  private connect(){
    try {
      this.ws = new WebSocket(this.url);
      this.ws.addEventListener('open', ()=>{ this.retry = 0; this.send({ t:'hello', id:this.id }); });
      this.ws.addEventListener('message', (ev)=>{ try { const data = JSON.parse(ev.data); this.listeners.forEach(l=>l(data)); } catch {} });
      this.ws.addEventListener('close', ()=>{ this.scheduleReconnect(); });
      this.ws.addEventListener('error', ()=>{ this.ws?.close(); });
    } catch { this.scheduleReconnect(); }
  }

  private scheduleReconnect(){
    if(this.retry > 5) return;
    const backoff = Math.min(5000, 500 * Math.pow(2, this.retry++));
    setTimeout(()=>this.connect(), backoff);
  }

  send(obj: any){
    if(this.ws && this.ws.readyState === WebSocket.OPEN){
      try { this.ws.send(JSON.stringify(obj)); } catch{}
    }
  }

  on(listener: Listener){ this.listeners.add(listener); return () => this.listeners.delete(listener); }

  close(){ try { this.ws?.close(); } catch {} }
}
