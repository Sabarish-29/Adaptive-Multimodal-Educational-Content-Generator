import { QueryClient } from '@tanstack/react-query';
import { persistQueryClient } from '@tanstack/react-query-persist-client';
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: 1,
    }
  }
});

// Persistence (skip during SSR / tests without window)
if (typeof window !== 'undefined') {
  const persister = createSyncStoragePersister({ storage: window.localStorage });
  persistQueryClient({
    queryClient,
    persister,
    maxAge: 1000 * 60 * 30, // 30 min
  });
}
