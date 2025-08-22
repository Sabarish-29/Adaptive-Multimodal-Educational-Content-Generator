import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { services } from '../../lib/api';

export function useLearnerProfile(learnerId: string, headers: Record<string,string>) {
  return useQuery({
    queryKey: ['learnerProfile', learnerId, headers.Authorization ? 'auth':'anon'],
    queryFn: async () => {
      const res = await axios.get(`${services.profiles}/v1/learners/${learnerId}/profile`, { headers });
      return res.data;
    },
    enabled: !!learnerId
  });
}
