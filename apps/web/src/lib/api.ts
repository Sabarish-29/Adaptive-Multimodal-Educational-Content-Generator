// Central API helpers. Prefer single gateway origin when NEXT_PUBLIC_API_GATEWAY is set.
const gateway = process.env.NEXT_PUBLIC_API_GATEWAY;
// When gateway present we use relative paths under /api/* so that cookies & CORS are unified.
export const services = gateway ? {
  profiles: '/api/profiles',
  adaptation: '/api/adaptation',
  sessions: '/api/sessions',
  content: '/api/content',
  analytics: '/api/analytics',
  recommendations: '/api/recommendations'
} : {
  profiles: process.env.NEXT_PUBLIC_PROFILES_URL || 'http://localhost:8004',
  adaptation: process.env.NEXT_PUBLIC_ADAPT_URL || 'http://localhost:8001',
  sessions: process.env.NEXT_PUBLIC_SESSIONS_URL || 'http://localhost:8003',
  content: process.env.NEXT_PUBLIC_CONTENT_URL || 'http://localhost:8002',
  analytics: process.env.NEXT_PUBLIC_ANALYTICS_URL || 'http://localhost:8005',
  recommendations: process.env.NEXT_PUBLIC_RECS_URL || 'http://localhost:8090'
};

export function withRid(url: string, rid: string){
  try {
    const u = new URL(url, typeof window === 'undefined' ? 'http://localhost:3000' : window.location.origin);
    u.searchParams.set('rid', rid);
    return u.toString();
  } catch {
    return url + (url.includes('?') ? '&' : '?') + 'rid=' + encodeURIComponent(rid);
  }
}
