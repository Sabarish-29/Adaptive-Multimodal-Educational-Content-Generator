import { useEffect, useRef, useState } from 'react';

export function useAsync<T>(fn: ()=>Promise<T>, deps: ReadonlyArray<any> = []): { data: T | null; error: any; loading: boolean; reload: ()=>void } {
  const [data, setData] = useState<T|null>(null);
  const [error, setError] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [tick, setTick] = useState(0);
  const cancelRef = useRef(false);
  // Cancellation effect
  useEffect(()=>{ cancelRef.current=false; return ()=>{ cancelRef.current=true; }; }, deps);
  // Execute async function when deps or tick change
  useEffect(()=>{
    let isActive = true;
    setLoading(true); setError(null);
    fn()
      .then(res=>{ if(isActive && !cancelRef.current) setData(res); })
      .catch(e=>{ if(isActive && !cancelRef.current) setError(e); })
      .finally(()=>{ if(isActive && !cancelRef.current) setLoading(false); });
    return ()=>{ isActive = false; };
  // Intentionally spread deps plus tick
  }, [fn, tick, ...deps]);
  return { data, error, loading, reload: ()=>setTick(t=>t+1) };
}
