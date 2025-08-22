import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { services } from '../../lib/api';
import { mark, markEnd, emitTelemetry } from '../../lib/telemetry';
import { retry } from '../../lib/retryFetch';

interface GeneratePayload { learner_id: string; unit_id: string; objectives: string[] }

interface LessonResult { data: any; headers: Record<string, any>; }
export function useGenerateLesson(headers: Record<string,string>) {
  return useMutation<LessonResult, Error, GeneratePayload>({
    mutationFn: async (payload: GeneratePayload) => {
      mark('generateLesson');
  const res = await retry(()=> axios.post(`${services.content}/v1/generate/lesson`, payload, { headers }), { attempts:3 });
      markEnd('generateLesson', 'api');
      emitTelemetry({ type:'lesson.generate', data:{ bytes: JSON.stringify(res.data||{}).length } });
      return { data: res.data, headers: res.headers as any };
  },
  meta: { successMessage: 'Lesson generated' }
  });
}
