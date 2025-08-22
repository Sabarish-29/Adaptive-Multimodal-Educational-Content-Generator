# Adaptive Edu Web

- `npm run e2e` Playwright e2e (requires dev server on :3000)

## Auth (Dev)
Mock login at `/login`. Any username accepted; containing `inst` -> instructor role. Token is mock base64 JSON stored in localStorage. Use `RouteGuard` to protect pages and restrict roles.

- `/author` (instructor only) markdown editor with autosave

- Authoring markdown editor (marked)

## E2E
Playwright specs in `e2e/`. Ensure browsers installed (`npx playwright install`). Start dev server, then run `npm run e2e`.


## Telemetry & Performance (Phase 8)

Lightweight client telemetry captures UX and performance signals.

Features:
- Batched event transport with queue cap (1000), exponential backoff + jitter retries.
- Web Vitals (CLS, LCP, INP, FID, TTFB) reported as `web_vital` events.
- Duration instrumentation: generate lesson (`gen.dur`), feedback submit (`feedback.dur`), navigation (`nav.dur`).
- Privacy: key blocklist (password, token, secret, auth, email, name, key).
- Overlay (optional) shows queue stats & recent vitals.

Env Flags:
```
NEXT_PUBLIC_FEATURE_TELEMETRY=true    # enable/disable telemetry globally
NEXT_PUBLIC_TELEMETRY_SAMPLE_RATE=1   # 0..1 sample rate
NEXT_PUBLIC_TELEMETRY_OVERLAY=true    # show in-app overlay panel
```

Debug:
- Call `window.__telemetry_flush()` in DevTools to force flush.

Testing:
- Unit tests (`telemetry.test.ts`) cover batching, flush thresholds, truncation, stats.
- Markdown sanitization (DOMPurify) for security
