import { useEffect, useState } from 'react';

// Returns true after first client render; false during SSR and initial hydration.
export function useHasMounted(){
  const [mounted, setMounted] = useState(false);
  useEffect(()=>{ setMounted(true); },[]);
  return mounted;
}
