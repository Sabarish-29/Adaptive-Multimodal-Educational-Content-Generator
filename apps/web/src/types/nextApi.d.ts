import type { Server as HTTPServer } from 'http';
import type { NextApiResponse } from 'next';
// Minimal interface for ws Server to avoid relying on external @types
// (We provide our own lightweight declaration instead of pulling full types.)
interface WebSocketLike { readyState: number; send(data:any): void; close(): void }
interface WebSocketServer { clients: Set<WebSocketLike>; }

export interface SocketServerWithWSS extends HTTPServer {
  wss?: WebSocketServer;
}

export interface NextApiResponseWithSocket extends NextApiResponse {
  socket: any & { server: SocketServerWithWSS };
}

// Allow importing 'ws' without full type package
declare module 'ws' {
  export class Server { constructor(opts?: any); handleUpgrade(req: any, socket: any, head: any, cb: (ws:any)=>void): void; clients: Set<any>; }
}
