declare module 'ws' {
  import { EventEmitter } from 'events';
  import { IncomingMessage } from 'http';
  export interface ServerOptions { noServer?: boolean }
  export class WebSocket extends EventEmitter {
    readyState: number;
    send(data: any): void;
    close(): void;
  }
  export class Server extends EventEmitter {
    constructor(opts?: ServerOptions);
    handleUpgrade(request: IncomingMessage, socket: any, head: any, cb: (ws: WebSocket) => void): void;
    clients: Set<WebSocket>;
  }
}
