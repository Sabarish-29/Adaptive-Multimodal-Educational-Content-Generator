import { useAuth } from './AuthContext';
import { useMemo } from 'react';

export function useAuthHeaders(){
  const { user } = useAuth();
  return useMemo(()=>{
    const reqId = crypto.randomUUID();
    if(!user) return { Authorization: '', 'X-Request-ID': reqId } as Record<string,string>;
    return { Authorization: `Bearer ${user.token}`, 'X-Request-ID': reqId } as Record<string,string>;
  },[user]);
}
