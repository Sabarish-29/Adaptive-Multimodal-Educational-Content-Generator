export interface RetryOptions { attempts?: number; baseDelayMs?: number; maxDelayMs?: number; factor?: number; signal?: AbortSignal }

export async function retry<T>(fn: ()=>Promise<T>, opts: RetryOptions = {}): Promise<T> {
  const { attempts = 4, baseDelayMs = 300, maxDelayMs = 4000, factor = 2, signal } = opts;
  let attempt = 0; let lastErr: any;
  while(attempt < attempts){
    if(signal?.aborted) throw new DOMException('aborted','AbortError');
    try { return await fn(); } catch (e:any){
      lastErr = e;
      attempt += 1;
      if(attempt >= attempts) break;
      const delay = Math.min(maxDelayMs, baseDelayMs * Math.pow(factor, attempt-1)) * (0.7 + Math.random()*0.6);
      await new Promise(res=>setTimeout(res, delay));
    }
  }
  throw lastErr;
}
