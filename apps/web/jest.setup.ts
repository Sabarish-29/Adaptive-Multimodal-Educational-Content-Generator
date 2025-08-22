import '@testing-library/jest-dom';

// Mock crypto.randomUUID for deterministic tests
if (!(global as any).crypto) {
	(global as any).crypto = {} as any;
}
(global as any).crypto.randomUUID = () => 'test-uuid';

// Basic EventSource mock
class MockEventSource {
	url: string; readyState = 0; onmessage: ((e: MessageEvent)=>void) | null = null; listeners: Record<string, Function[]> = {};
	constructor(url: string){ this.url = url; (global as any).__eventSources.push(this); setTimeout(()=>{ this.readyState = 1; }, 0); }
	addEventListener(type: string, cb: any){ (this.listeners[type] ||= []).push(cb); }
	dispatch(type: string, data: any){ const evt = { data: JSON.stringify(data) } as MessageEvent; if(type==='message' && this.onmessage) this.onmessage(evt); (this.listeners[type]||[]).forEach(f=>f(evt)); }
	close(){ this.readyState = 2; }
}
(global as any).__eventSources = [];
(global as any).EventSource = MockEventSource as any;

