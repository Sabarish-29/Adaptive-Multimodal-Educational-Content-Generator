import React, { useState, useEffect, useCallback, useRef } from 'react';
import { emitTelemetry } from '../lib/telemetry';
import { computeLineDiff } from '../lib/diff';
import { AppShell } from '../components/layout/AppShell';
import { useAuth } from '../auth/AuthContext';
import { RouteGuard } from '../components/RouteGuard';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Stack } from '../components/Stack';
import { marked } from 'marked';
import katex from 'katex';
import { CollabSocket, CollabCursor } from '../lib/collabSocket';
import { lintMarkdown, LintIssue } from '../lib/markdownLint';
import DOMPurify from 'dompurify';
import { yText } from '../lib/collabDoc';

interface FrontMatter { title?: string; objectives?: string[]; [k: string]: any }
interface ParsedDoc { frontmatter: FrontMatter; body: string }

export function parseFrontmatter(src: string): ParsedDoc {
  if(src.startsWith('---')){
    const end = src.indexOf('\n---', 3);
    if(end !== -1){
      const fmBlock = src.slice(3, end).trim();
      const body = src.slice(end+4);
      const fm: FrontMatter = {};
      fmBlock.split(/\r?\n/).forEach(line=>{
        const m = line.match(/^([A-Za-z0-9_\-]+):\s*(.*)$/);
        if(m){
          const key = m[1];
          let val: any = m[2];
          if(val.includes(',')) val = val.split(',').map((s: string)=>s.trim()).filter(Boolean);
          fm[key] = val;
        }
      });
      return { frontmatter: fm, body };
    }
  }
  return { frontmatter: {}, body: src };
}

// Strict DOMPurify config (guarded for SSR; DOMPurify setConfig not available during Next.js build)
const purifier = DOMPurify;
if (typeof window !== 'undefined' && (purifier as any).setConfig) {
  (purifier as any).setConfig({
  ALLOWED_TAGS: ['h1','h2','h3','h4','h5','h6','p','ul','ol','li','strong','em','code','pre','blockquote','a','img','table','thead','tbody','tr','th','td','hr','span'],
  ALLOWED_ATTR: ['href','src','alt','title','class'],
    FORCE_BODY: true
  });
}

function Editor(){
  const key = 'draft:md';
  const [raw, setRaw] = useState(`---\ntitle: Lesson Draft\nobjectives: addition, subtraction\n---\n\n## Introduction\n\nStart writing...`);
  const [html, setHtml] = useState('');
  const [dirty, setDirty] = useState(false);
  const [lastSaved, setLastSaved] = useState<number | null>(null);
  const [fm, setFm] = useState<FrontMatter>({});
  // Presence (Phase 10 D - intra-tab via BroadcastChannel)
  const [peers, setPeers] = useState<Record<string,{ id:string; name?:string; ts:number }>>({});
  const selfIdRef = useRef<string>('');
  if(!selfIdRef.current){
    try {
      const existing = localStorage.getItem('author:presence:id');
      if(existing) selfIdRef.current = existing; else {
        const nid = crypto.randomUUID().slice(0,8);
        localStorage.setItem('author:presence:id', nid);
        selfIdRef.current = nid;
      }
    } catch { selfIdRef.current = 'self'; }
  }
  const [parsing, setParsing] = useState(false);
  // Collaboration (Phase 11 - realtime cursors via websocket)
  const collabRef = useRef<CollabSocket | null>(null);
  const [cursors, setCursors] = useState<Record<string, CollabCursor>>({});
  const cursorSendRef = useRef<number>(0);
  const undoStack = useRef<string[]>([]);
  const redoStack = useRef<string[]>([]);
  // Phase 10 A: local snapshot history (versioning) - ring buffer of last 20 saves
  const snapshotsRef = useRef<{ ts: number; raw: string }[]>([]);
  const [showDiff, setShowDiff] = useState(false);
  const [diffIndex, setDiffIndex] = useState<number|null>(null); // index into snapshots (from end)
  const workerRef = useRef<Worker | null>(null);
  const parseReqId = useRef(0);
  const [lintIssues, setLintIssues] = useState<LintIssue[]>([]);
  useEffect(()=>{
    if(typeof window === 'undefined') return;
    try {
      // Web worker for markdown parsing (off main thread)
      // @ts-ignore
      const w = new Worker(new URL('../workers/markdownWorker.ts', import.meta.url));
      w.onmessage = (e: MessageEvent) => {
        const { id, html: workerHtml } = e.data || {};
        if(id !== parseReqId.current) return; // stale
        const clean = purifier.sanitize(workerHtml || '');
        setHtml(clean);
        setParsing(false);
        setDirty(true);
      };
      workerRef.current = w;
      return () => { w.terminate(); };
    } catch {
      workerRef.current = null; // fallback will be inline
    }
  },[]);
  // Collaboration websocket init
  useEffect(()=>{
    if(typeof window === 'undefined') return;
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    // Assumption: server exposes /api/collab endpoint that echoes protocol messages
    const url = `${proto}://${window.location.host}/api/collab`;
    try {
      const sock = new CollabSocket(url, selfIdRef.current);
      collabRef.current = sock;
      const off = sock.on((msg:any)=>{
        if(!msg || msg.id === selfIdRef.current) return;
        if(msg.t === 'cursor' && typeof msg.line==='number' && typeof msg.ch==='number'){
          setCursors(prev => ({ ...prev, [msg.id]: { id: msg.id, line: msg.line, ch: msg.ch, ts: Date.now() } }));
          emitTelemetry({ type:'collab.cursor.recv', data:{ from: msg.id } });
        }
        if(msg.t === 'presence'){
          emitTelemetry({ type:'collab.presence.recv', data:{ from: msg.id } });
        }
      });
      // Periodic presence & cleanup stale cursors
      const int = setInterval(()=>{
  sock.send({ t:'presence', id:selfIdRef.current });
  emitTelemetry({ type:'collab.presence.send' });
        setCursors(prev => { const now = Date.now(); const next: typeof prev = {}; Object.values(prev).forEach(c=>{ if(now-c.ts < 8000) next[c.id]=c; }); return next; });
      }, 4000);
      return ()=>{ off(); clearInterval(int); sock.close(); };
    } catch { /* ignore */ }
  },[]);
  useEffect(()=>{ const s = localStorage.getItem(key); if(s) setRaw(s); },[]);
  // Presence channel
  useEffect(()=>{
    if(typeof window === 'undefined' || !(window as any).BroadcastChannel) return;
    const bc = new BroadcastChannel('author_presence');
    const send = () => bc.postMessage({ t:'presence', id:selfIdRef.current, ts: Date.now() });
    const onMsg = (e: MessageEvent) => {
      const d = e.data;
      if(d?.t==='presence' && d.id !== selfIdRef.current){
        setPeers(p=>{ const np = { ...p, [d.id]: { id:d.id, ts:d.ts } }; return np; });
      }
    };
    bc.addEventListener('message', onMsg);
    send();
    const int = setInterval(()=>{ send(); setPeers(p=>{ const now=Date.now(); const np: typeof p = {}; Object.values(p).forEach(v=>{ if(now - v.ts < 10000) np[v.id]=v; }); return np; }); }, 4000);
    return ()=>{ clearInterval(int); bc.removeEventListener('message', onMsg); bc.close(); };
  },[]);
  // Parse & sanitize (debounced for performance)
  useEffect(()=>{
    const h = setTimeout(()=>{
      const { frontmatter, body } = parseFrontmatter(raw);
      setFm(frontmatter);
      setParsing(true);
      parseReqId.current += 1;
      const id = parseReqId.current;
      const render = (mdBody: string) => {
        // Simple math replacement: block $$...$$ and inline $...$
        const mathBlocks: string[] = [];
        const placeholder = (i:number)=>`@@MATH_BLOCK_${i}@@`;
        mdBody = mdBody.replace(/\$\$([\s\S]+?)\$\$/g, (_,expr)=>{ const html = katex.renderToString(expr.trim(), { throwOnError:false, displayMode:true }); mathBlocks.push(html); return placeholder(mathBlocks.length-1); });
        mdBody = mdBody.replace(/(?<!\$)\$([^\n$]+?)\$(?!\$)/g, (_,expr)=>{ const html = katex.renderToString(expr.trim(), { throwOnError:false, displayMode:false }); mathBlocks.push(html); return placeholder(mathBlocks.length-1); });
        let dirtyMd = marked.parse(mdBody) as string;
        // Restore placeholders
        dirtyMd = dirtyMd.replace(/@@MATH_BLOCK_(\d+)@@/g, (_,i)=> mathBlocks[Number(i)] || '');
        const clean = purifier.sanitize(dirtyMd);
        setHtml(clean); setParsing(false); setDirty(true);
      };
      if(workerRef.current){
        try { workerRef.current.postMessage({ id, body }); render(body); } catch { render(body); }
      } else { render(body); }
    }, 150);
    return ()=>clearTimeout(h);
  },[raw]);
  // Lint on debounce
  useEffect(()=>{
    const h = setTimeout(()=>{ setLintIssues(lintMarkdown(raw)); }, 250);
    return ()=>clearTimeout(h);
  },[raw]);
  // Persist (configurable autosave delay)
  useEffect(()=>{
    if(!dirty) return;
    const autosaveMs = Number(process.env.NEXT_PUBLIC_AUTHOR_AUTOSAVE_MS || 600);
    const t = setTimeout(()=>{
      localStorage.setItem(key, raw);
      setLastSaved(Date.now());
      setDirty(false);
  // Capture snapshot (Phase 10 A)
  snapshotsRef.current.push({ ts: Date.now(), raw });
  if(snapshotsRef.current.length > 20) snapshotsRef.current.shift();
      emitTelemetry({ type:'snapshot.save', data:{ size: raw.length } });
    }, 600);
    return ()=>clearTimeout(t);
  },[dirty, raw]);
  const onChange = (v: string) => {
    undoStack.current.push(raw);
    if(undoStack.current.length>100) undoStack.current.shift();
    redoStack.current = [];
    // CRDT propagate (local -> yText)
    try {
      if(crdtReadyRef.current){
        const current = yText.toString();
        if(current !== v){
          crdtUpdatingRef.current = true;
          yText.doc?.transact(()=>{
            yText.delete(0, yText.length);
            yText.insert(0, v);
          });
          crdtUpdatingRef.current = false;
          emitTelemetry({ type:'collab.crdt.update.local', data:{ size: v.length } });
        }
      }
    } catch { /* ignore */ }
    setRaw(v);
  };
  // Track cursor position & broadcast
  const textAreaRef = useRef<HTMLTextAreaElement|null>(null);
  const computePos = () => {
    const el = textAreaRef.current; if(!el) return null;
    const idx = el.selectionStart || 0;
    const pre = raw.slice(0, idx);
    const lines = pre.split(/\n/);
    const line = lines.length - 1;
    const ch = lines[lines.length-1].length;
    return { line, ch };
  };
  const broadcastCursor = () => {
    const now = Date.now();
    if(now - cursorSendRef.current < 80) return; // throttle ~12/s
    cursorSendRef.current = now;
    const pos = computePos();
    if(pos && collabRef.current){
  collabRef.current.send({ t:'cursor', id:selfIdRef.current, ...pos });
  emitTelemetry({ type:'collab.cursor.send', data:{ line: pos.line, ch: pos.ch } });
    }
  };
  // --- CRDT (Yjs) integration ---
  const crdtReadyRef = useRef(false);
  const crdtUpdatingRef = useRef(false);
  useEffect(()=>{
    if(typeof window === 'undefined') return;
    if(crdtReadyRef.current) return;
    try {
      // Initialize shared text from existing yText OR seed with local raw
      if(yText.length === 0){
        yText.insert(0, raw);
      } else {
        const txt = yText.toString();
        if(txt !== raw) setRaw(txt);
      }
      emitTelemetry({ type:'collab.crdt.init', data:{ size: yText.length } });
      const observer = () => {
        if(crdtUpdatingRef.current) return; // ignore local echo
        const txt = yText.toString();
        setRaw(prev => (prev === txt ? prev : txt));
        emitTelemetry({ type:'collab.crdt.update.remote', data:{ size: txt.length } });
      };
      yText.observe(observer);
      crdtReadyRef.current = true;
      return () => { yText.unobserve(observer); };
    } catch { /* ignore */ }
  },[raw]);
  const onSelectionChange = () => { broadcastCursor(); };
  const undo = useCallback(()=>{
    const prev = undoStack.current.pop();
    if(prev!=null){ redoStack.current.push(raw); setRaw(prev); }
  },[raw]);
  const redo = useCallback(()=>{
    const nxt = redoStack.current.pop();
    if(nxt!=null){ undoStack.current.push(raw); setRaw(nxt); }
  },[raw]);
  const updateFrontmatterField = (field: string, value: string) => {
    setRaw(prev => {
      const { frontmatter, body } = parseFrontmatter(prev);
      const fmNext: Record<string, any> = { ...frontmatter };
      if(field === 'objectives'){
        const arr = value.split(',').map(s=>s.trim()).filter(Boolean);
        if(arr.length) fmNext[field] = arr; else delete fmNext[field];
      } else {
        if(value.trim()) fmNext[field] = value.trim(); else delete fmNext[field];
      }
      const lines = Object.entries(fmNext).map(([k,v]) => `${k}: ${Array.isArray(v)? v.join(', ') : v}`);
      const fmBlock = lines.length ? `---\n${lines.join('\n')}\n---\n` : '';
      return fmBlock + body.replace(/^\n+/,'');
    });
  };
  const addObjective = (text: string) => {
    if(!text.trim()) return;
    updateFrontmatterField('objectives', [ ...(Array.isArray(fm.objectives)? fm.objectives: typeof fm.objectives==='string'? [fm.objectives]: []), text.trim() ].join(', '));
  };
  const removeObjective = (idx: number) => {
    if(!Array.isArray(fm.objectives)) return;
    const next = fm.objectives.filter((_,i)=>i!==idx);
    updateFrontmatterField('objectives', next.join(', '));
  };
  const moveObjective = (idx: number, dir: -1|1) => {
    if(!Array.isArray(fm.objectives)) return;
    const next = [...fm.objectives];
    const ni = idx + dir;
    if(ni<0 || ni>=next.length) return;
    const [item] = next.splice(idx,1);
    next.splice(ni,0,item);
    updateFrontmatterField('objectives', next.join(', '));
  };
  const newObjRef = useRef<HTMLInputElement|null>(null);
  const chipBtnStyle: React.CSSProperties = { background:'transparent', border:'none', color:'#9CA3AF', cursor:'pointer', fontSize:11, padding:0, lineHeight:1 };
  const exportJson = () => {
    const { frontmatter, body } = parseFrontmatter(raw);
    const doc = { ...frontmatter, body };
    const blob = new Blob([JSON.stringify(doc,null,2)], { type:'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = (frontmatter.title || 'lesson') + '.json'; a.click();
    URL.revokeObjectURL(url);
  };
  const restoreSnapshot = (sRaw: string) => { setRaw(sRaw); emitTelemetry({ type:'snapshot.restore' }); };
  const diffView = () => {
    if(diffIndex==null) return null;
    const snaps = snapshotsRef.current;
    const target = snaps[snaps.length-1-diffIndex];
    if(!target) return null;
  const diff = computeLineDiff(target.raw, raw);
    return (
      <div style={{ maxHeight:300, overflowY:'auto', fontFamily:'monospace', fontSize:11, background:'#11151b', border:'1px solid #2A303B', borderRadius:6, padding:8 }}>
        {diff.map((d,i)=>(
          <div key={i} style={{ whiteSpace:'pre' }}>
            {d.type==='add' && <span style={{ color:'#10B981' }}>+ {d.text}</span>}
            {d.type==='del' && <span style={{ color:'#EF4444' }}>- {d.text}</span>}
            {d.type==='ctx' && <span style={{ opacity:.6 }}>  {d.text}</span>}
          </div>
        ))}
      </div>
    );
  };
  const words = raw.replace(/---[\s\S]*?---/,'').trim().split(/\s+/).filter(Boolean).length;
  const chars = raw.length;
  const readMin = Math.max(1, Math.round(words/200));
  return (
    <Stack gap={20}>
      <Card title="Markdown" actions={
        <div style={{ display:'flex', gap:8 }}>
          <Button size="sm" variant="secondary" onClick={()=>{ localStorage.removeItem(key); setRaw(''); }}>Clear</Button>
          <Button size="sm" variant="ghost" onClick={undo} disabled={!undoStack.current.length}>Undo</Button>
          <Button size="sm" variant="ghost" onClick={redo} disabled={!redoStack.current.length}>Redo</Button>
          <Button size="sm" variant="secondary" onClick={exportJson}>Export JSON</Button>
        </div>
      }>
        <label htmlFor="author-markdown" style={{ fontSize:12, opacity:.75, display:'block', marginBottom:4 }}>Markdown source</label>
        <div style={{ position:'relative' }}>
          <textarea
            ref={textAreaRef}
            id="author-markdown"
            aria-label="Markdown editor"
            value={raw}
            onChange={e=>{ onChange(e.target.value); broadcastCursor(); }}
            onClick={onSelectionChange}
            onKeyUp={onSelectionChange}
            onSelect={onSelectionChange}
            rows={14}
            style={{ width:'100%', fontFamily:'monospace', fontSize:13, background:'#161A21', color:'inherit', border:'1px solid #2A303B', borderRadius:6, padding:10 }}
          />
          {/* Remote cursors */}
          {Object.values(cursors).filter(c=>c.id!==selfIdRef.current).map(c=>{
            // Map id -> deterministic color
            const hue = (c.id.split('').reduce((a,ch)=>a+ch.charCodeAt(0),0) % 360);
            const color = `hsl(${hue} 70% 55%)`;
            // Approximate position: measure line height via 1em assumption
            const lineHeight = 20; // px (matches typical 13px font + padding)
            const top = 10 + c.line * lineHeight; // textarea padding top + line offset
            const left = 12 + c.ch * 7; // rough mono char width estimate
            const key = c.id;
            return (
              <div key={key} style={{ position:'absolute', top, left, pointerEvents:'none', transform:'translateY(-2px)' }}>
                <div style={{ width:2, height:lineHeight-4, background:color, borderRadius:1 }} />
                <div style={{ position:'absolute', top:-14, left:4, background:color, color:'#11151b', fontSize:10, padding:'1px 4px', borderRadius:4, whiteSpace:'nowrap' }}>{c.id}</div>
              </div>
            );
          })}
        </div>
        <p style={{ margin:'8px 0 0', fontSize:11, opacity:.7 }}>{dirty ? 'Saving…' : lastSaved ? `Saved ${Math.round((Date.now()-lastSaved)/1000)}s ago` : 'Not saved yet'} | {words} words • {chars} chars • ~{readMin} min read</p>
      </Card>
      <Card title="Metadata" compact>
        <div style={{ fontSize:12, display:'flex', flexDirection:'column', gap:8 }}>
          <label style={{ display:'flex', flexDirection:'column', gap:4 }}>
            <span style={{ fontSize:11, opacity:.7 }}>Title</span>
            <input data-testid="title-input" value={typeof fm.title==='string'? fm.title : ''} onChange={e=>updateFrontmatterField('title', e.target.value)} placeholder="Lesson title" style={{ background:'#11151b', border:'1px solid #2A303B', borderRadius:4, padding:'4px 6px', fontSize:12, color:'#E5E7EB' }} />
          </label>
          <label style={{ display:'flex', flexDirection:'column', gap:4 }}>
            <span style={{ fontSize:11, opacity:.7 }}>Objectives (comma separated)</span>
            <input data-testid="objectives-input" value={Array.isArray(fm.objectives)? fm.objectives.join(', ') : (typeof fm.objectives==='string'? fm.objectives : '')} onChange={e=>updateFrontmatterField('objectives', e.target.value)} placeholder="objective a, objective b" style={{ background:'#11151b', border:'1px solid #2A303B', borderRadius:4, padding:'4px 6px', fontSize:12, color:'#E5E7EB' }} />
          </label>
          <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
            <span style={{ fontSize:11, opacity:.7 }}>Objectives (chips)</span>
            <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
              {Array.isArray(fm.objectives) && fm.objectives.map((o,i)=>(
                <div key={i} style={{ display:'flex', alignItems:'center', gap:4, background:'#1E2430', border:'1px solid #2A303B', borderRadius:16, padding:'4px 8px', fontSize:11 }}>
                  <span>{o}</span>
                  <div style={{ display:'flex', gap:2 }}>
                    <button aria-label={`Move ${o} up`} disabled={i===0} onClick={()=>moveObjective(i,-1)} style={chipBtnStyle}>↑</button>
                    <button aria-label={`Move ${o} down`} disabled={i===fm.objectives!.length-1} onClick={()=>moveObjective(i,1)} style={chipBtnStyle}>↓</button>
                    <button aria-label={`Remove ${o}`} onClick={()=>removeObjective(i)} style={chipBtnStyle}>✕</button>
                  </div>
                </div>
              ))}
              {(!fm.objectives || (Array.isArray(fm.objectives)&&!fm.objectives.length)) && <span style={{ fontSize:11, opacity:.5 }}>None</span>}
            </div>
            <div style={{ display:'flex', gap:6 }}>
              <input ref={newObjRef} placeholder="New objective" style={{ flex:1, background:'#11151b', border:'1px solid #2A303B', borderRadius:4, padding:'4px 6px', fontSize:12, color:'#E5E7EB' }} />
              <button onClick={()=>{ if(newObjRef.current){ addObjective(newObjRef.current.value); newObjRef.current.value=''; newObjRef.current.focus(); } }} style={{ background:'#374151', border:'1px solid #4B5563', color:'#E5E7EB', fontSize:11, padding:'4px 10px', borderRadius:4, cursor:'pointer' }}>Add</button>
            </div>
          </div>
          <div style={{ fontSize:11, opacity:.6 }}>Words: {words} • Chars: {chars} • ~{readMin} min read {parsing && <span style={{ marginLeft:6, color:'#6366F1' }}>parsing…</span>}</div>
        </div>
      </Card>
      <Card title="Preview" aria-label="Preview">
        <div style={{ fontSize:14, lineHeight:1.5 }} dangerouslySetInnerHTML={{ __html: html }} />
      </Card>
      <Card title="History" compact>
        <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
          {!snapshotsRef.current.length && <p style={{ fontSize:11, opacity:.6, margin:0 }}>No snapshots yet.</p>}
          {snapshotsRef.current.slice().reverse().slice(0,8).map((s,idx) => (
            <div key={s.ts} style={{ display:'flex', gap:6 }}>
              <button onClick={()=>restoreSnapshot(s.raw)} style={{ flex:1, textAlign:'left', fontSize:11, background:'#161A21', border:'1px solid #2A303B', borderRadius:4, padding:'4px 6px', cursor:'pointer' }}>
                {new Date(s.ts).toLocaleTimeString()} · {s.raw.length} chars
              </button>
              <button aria-label="Diff" onClick={()=>{ setDiffIndex(idx); setShowDiff(true); emitTelemetry({ type:'snapshot.diff.open' }); }} style={{ background:'#1E1B4B', border:'1px solid #4338CA', color:'#C7D2FE', fontSize:11, padding:'4px 6px', borderRadius:4, cursor:'pointer' }}>Diff</button>
            </div>
          ))}
          <div style={{ display:'flex', gap:6 }}>
            <button onClick={()=>{ snapshotsRef.current.push({ ts: Date.now(), raw }); emitTelemetry({ type:'snapshot.save.manual' }); }} style={{ flex:1, background:'#374151', border:'1px solid #4B5563', color:'#E5E7EB', fontSize:11, padding:'4px 6px', borderRadius:4, cursor:'pointer' }}>Snapshot Now</button>
            <button disabled={diffIndex==null} onClick={()=>{ setShowDiff(false); setDiffIndex(null); }} style={{ background:'#11151b', border:'1px solid #2A303B', color:'#9CA3AF', fontSize:11, padding:'4px 6px', borderRadius:4, cursor:'pointer' }}>Close Diff</button>
          </div>
          {showDiff && diffView()}
        </div>
      </Card>
      <Card title="Presence" compact>
        <div style={{ display:'flex', flexWrap:'wrap', gap:6, fontSize:11 }}>
          <div style={{ background:'#161A21', border:'1px solid #2A303B', padding:'4px 8px', borderRadius:12 }}>You ({selfIdRef.current})</div>
          {Object.values(peers).map(p => (
            <div key={p.id} style={{ background:'#161A21', border:'1px solid #2A303B', padding:'4px 8px', borderRadius:12 }}>{p.id}</div>
          ))}
          {!Object.keys(peers).length && <span style={{ opacity:.5 }}>No other editors</span>}
        </div>
      </Card>
      <Card title={`Lint (${lintIssues.length})`} compact>
        {!lintIssues.length && <div style={{ fontSize:11, opacity:.6 }}>No issues</div>}
        {!!lintIssues.length && (
          <ul style={{ listStyle:'none', padding:0, margin:0, maxHeight:180, overflowY:'auto', fontSize:11, display:'flex', flexDirection:'column', gap:4 }}>
            {lintIssues.slice(0,50).map((i,idx)=>(
              <li key={idx} style={{ background:i.severity==='error'? '#3B1D1D':'#242B38', border:'1px solid #2A303B', borderLeft:`3px solid ${i.severity==='error'?'#EF4444':'#F59E0B'}`, padding:'4px 6px', borderRadius:4 }}>
                <strong style={{ fontWeight:600 }}>{i.severity.toUpperCase()}</strong> {i.message}{i.line && <span style={{ opacity:.6 }}> (line {i.line})</span>}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </Stack>
  );
}

// Setup collaboration socket side-effect outside render body hooks cluster
// (placed after component definition for clarity but within same file)
// Hook into lifecycle inside component via useEffect below.

// Extend Editor with collaboration effect
// (We append effect after definition for patch minimalism)
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function useEditorCollabEffects(){ /* no-op placeholder to mark section */ }

// Inject effect by re-opening component scope through prototype mutation (not typical; we instead patch inside component below)

// NOTE: Re-open Editor component to add collaboration effect (patch-friendly)
// We can't actually re-open the function, so collaboration effect added inside initial function above via useEffect below.

// (Add at end of file side-effect free)

// Collaboration effect appended: we'll rely on a second patch region inside component.

function Page(){
  const { user } = useAuth();
  return (
  <AppShell title="Author" nav={[{label:'Home', href:'/'},{label:'Analytics', href:'/analytics'},{label:'Content', href:'/content'},{label:'Sessions', href:'/sessions'},{label:'Author', href:'/author'},{label:'Telemetry', href:'/telemetry'}]}>
      <div style={{ maxWidth:1100, margin:'0 auto', padding:32 }}>
        <h2 style={{ margin:'0 0 12px' }}>Authoring Workspace</h2>
        <p style={{ margin:'0 0 24px', fontSize:14, opacity:.8 }}>Write and preview lesson content in Markdown. (Instructor only)</p>
        {user && <Editor />}
      </div>
    </AppShell>
  );
}

import { useHasMounted } from '../hooks/useHasMounted';
export default function AuthorPage(){
  const mounted = useHasMounted();
  if(!mounted){
    return <div style={{padding:40,fontSize:12,opacity:.6}}>Loading authoring…</div>;
  }
  return <RouteGuard roles={['instructor']}><Page/></RouteGuard>;
}
