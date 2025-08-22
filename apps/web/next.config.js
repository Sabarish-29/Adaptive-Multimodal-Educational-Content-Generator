const withBundleAnalyzer = require('@next/bundle-analyzer')({ enabled: process.env.ANALYZE === 'true' });

// If a gateway base is provided (e.g. http://localhost:9000) we proxy frontend /api/* requests to it during dev.
// This allows client code to use relative paths while still reaching the FastAPI gateway.
// Prefer gateway by default during local dev to simplify setup
const gateway = process.env.NEXT_PUBLIC_API_GATEWAY || (process.env.NODE_ENV !== 'production' ? 'http://localhost:9090' : undefined); // e.g. http://localhost:9090

// Allow disabling lint/typecheck during container builds
const disableLint = process.env.NEXT_DISABLE_ESLINT_PLUGIN === 'true';
const disableTypecheck = process.env.NEXT_DISABLE_TYPECHECK === 'true';

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // Skip ESLint during `next build` when flagged (e.g., Docker)
    ignoreDuringBuilds: disableLint,
  },
  typescript: {
    // Skip TS type errors during `next build` when flagged (e.g., Docker)
    ignoreBuildErrors: disableTypecheck,
  },
  async headers(){
    if(process.env.NODE_ENV !== 'production') return [];
    return [
      {
        source: '/(.*)',
        headers: [
          { key:'Referrer-Policy', value:'strict-origin-when-cross-origin' },
          { key:'X-Content-Type-Options', value:'nosniff' },
          { key:'X-DNS-Prefetch-Control', value:'off' },
          { key:'Cross-Origin-Opener-Policy', value:'same-origin' },
          { key:'Cross-Origin-Embedder-Policy', value:'require-corp' },
          { key:'Cross-Origin-Resource-Policy', value:'same-origin' },
          { key:'Permissions-Policy', value:'camera=(), microphone=(), geolocation=()' }
        ]
      }
    ];
  },
  async rewrites(){
    if(!gateway) return [];
    // Preserve path after /api/ when forwarding to gateway
    return [
      {
        source: '/api/:path*',
        destination: `${gateway.replace(/\/$/, '')}/api/:path*`
      }
    ];
  }
};

module.exports = withBundleAnalyzer(nextConfig);
