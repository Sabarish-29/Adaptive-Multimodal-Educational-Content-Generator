import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { services } from '../../lib/api';

export function useAnalyticsProgress(learnerId: string, headers: Record<string,string>) {
  return useQuery({
    queryKey: ['analyticsProgress', learnerId],
    queryFn: async () => {
      const res = await axios.get(`${services.analytics}/v1/analytics/learner/${learnerId}/progress`, { headers });
      return res.data;
    },
    enabled: !!learnerId
  });
}
