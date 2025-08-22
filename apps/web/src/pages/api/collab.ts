import type { NextApiRequest } from 'next';
import { Server } from 'ws';
import { decodeMockToken } from '../../../src/auth/AuthContext';
// Type helper (ambient declaration in src/types/nextApi.d.ts)
import type { NextApiResponseWithSocket } from '../../../src/types/nextApi';

// We need a module-scoped server so Next.js hot reload doesn't create multiples.
let wss: Server | undefined;

interface CursorMsg { t: 'cursor'; id: string; line: number; ch: number }
interface HelloMsg { t: 'hello'; id: string }
interface PresenceMsg { t: 'presence'; id: string }

type Msg = CursorMsg | HelloMsg | PresenceMsg;

function isMsg(data: any): data is Msg { return data && typeof data.t === 'string'; }

export const config = { runtime: 'nodejs' };

export default function handler(req: NextApiRequest & { socket: any }, res: NextApiResponseWithSocket) {
  if(!res.socket.server.wss){
    // Create once
    wss = new Server({ noServer: true });
    // Upgrade handling
    res.socket.server.on('upgrade', (request: any, socket: any, head: any) => {
      if(!request.url.includes('/api/collab')) return;
      // Extract token from query ?token= or from cookie auth_user
      let token: string | null = null;
      try {
        const u = new URL(request.url, 'http://localhost');
        token = u.searchParams.get('token');
        if(!token && request.headers.cookie){
          const m = /auth:user=([^;]+)/.exec(request.headers.cookie);
          if(m){
            try { const decoded = decodeURIComponent(m[1]); const obj = JSON.parse(decoded); token = obj.token; } catch {}
          }
        }
      } catch {}
      const payload = token ? decodeMockToken(token) : null;
      if(!payload || payload.role !== 'instructor'){
        socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
        socket.destroy();
        return;
      }
      wss!.handleUpgrade(request, socket, head, (ws: any) => {
        wss!.emit('connection', ws, request);
      });
    });
    wss.on('connection', (socket: any) => {
      socket.on('message', (raw: Buffer) => {
        let msg: any;
        try { msg = JSON.parse(raw.toString()); } catch { return; }
        if(!isMsg(msg)) return;
        // Simple broadcast (no auth yet)
        const payload = JSON.stringify(msg);
        wss!.clients.forEach((client: any) => { if(client.readyState === 1) client.send(payload); });
      });
    });
    res.socket.server.wss = wss;
  }
  res.status(200).json({ ok: true });
}
