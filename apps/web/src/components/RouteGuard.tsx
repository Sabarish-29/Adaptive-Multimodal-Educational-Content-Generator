import React, { useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useRouter } from 'next/router';

interface RouteGuardProps { requireAuth?: boolean; roles?: Array<'learner'|'instructor'> }

export const RouteGuard: React.FC<React.PropsWithChildren<RouteGuardProps>> = ({ requireAuth=true, roles, children }) => {
  const { user } = useAuth();
  const router = useRouter();
  useEffect(()=>{
    if(requireAuth && !user){ router.replace('/login'); return; }
    if(roles && user && !roles.includes(user.role)){ router.replace('/'); }
  },[requireAuth, user, roles, router]);
  if(requireAuth && !user) return null;
  if(roles && user && !roles.includes(user.role)) return null;
  return <>{children}</>;
};
