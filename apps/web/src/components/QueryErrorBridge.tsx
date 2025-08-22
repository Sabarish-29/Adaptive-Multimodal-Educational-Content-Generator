import React, { useEffect } from 'react';
import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { useToast } from './Toast';
import { QueryClientProvider } from '@tanstack/react-query';

// NOTE: This component assumes it is rendered inside providers for React Query & Toast
export const QueryErrorObserver: React.FC<{ error?: unknown }> = ({ error }) => {
  const { push } = useToast();
  useEffect(()=>{
    if(error){
      const msg = (error as any)?.message || 'Unknown error';
      push({ message: msg, type:'error' });
    }
  },[error, push]);
  return null;
};
