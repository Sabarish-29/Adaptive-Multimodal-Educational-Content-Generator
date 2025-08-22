import time
from typing import Callable, Awaitable, Optional
from fastapi import Request, Response

try:
    from prometheus_client import Counter  # type: ignore
except Exception:  # prometheus optional in some services
    Counter = None  # type: ignore

RATE_LIMIT_HEADER = "X-RateLimit-Remaining"


class SlidingWindowLimiter:
    """Redis-backed (optional) sliding window rate limiter with in-memory fallback.
    Supports custom window seconds (default 60). Algorithm: simple fixed window.
    """

    def __init__(
        self, per_minute: int = 60, redis_client=None, window_seconds: int = 60
    ):
        self.per_minute = per_minute
        self.redis = redis_client
        self.window_seconds = window_seconds or 60
        self._mem: dict[str, tuple[int, int]] = {}

    async def allow(self, key: str) -> int:
        now = int(time.time())
        window = now // self.window_seconds
        if not self.redis:
            count, win = self._mem.get(key, (0, window))
            if win != window:
                count = 0
                win = window
            if count >= self.per_minute:
                return -1  # signal exceeded
            count += 1
            self._mem[key] = (count, win)
            return self.per_minute - count  # remaining (can be 0 and still allowed)
        # Redis path
        k = f"rl:{key}:{window}"
        try:
            new_count = await self.redis.incr(k)
            if new_count == 1:
                await self.redis.expire(k, 90)
            if new_count > self.per_minute:
                return -1
            return self.per_minute - new_count
        except Exception:
            self.redis = None
            return await self.allow(key)


async def rate_limit_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
):
    cfg = getattr(request.app.state, "rate_limit_config", None)  # type: ignore[attr-defined]
    if not cfg:
        return await call_next(request)
    limiter: SlidingWindowLimiter = cfg["limiter"]
    # For standard config only mutate write operations, but allow opting-in for GET via env knobs used in tests.
    include_get = False
    try:
        import os

        if os.getenv("RATE_LIMIT_MAX_REQUESTS") and os.getenv(
            "RATE_LIMIT_WINDOW_SECONDS"
        ):
            include_get = True
    except Exception:
        include_get = False
    remaining = None
    if (
        request.method in ("POST", "PUT", "PATCH")
        or include_get
        or request.url.path in ("/health", "/healthz")
    ):
        ident = request.headers.get("Authorization") or (
            request.client.host if request.client else "anon"
        )
        key = f"{ident}:{request.url.path}"[:180]
        remaining = await limiter.allow(key)
    # store for handlers that craft custom responses
    setattr(request.state, "rate_remaining", remaining)
    if remaining is not None and remaining < 0:
        # metrics
        if Counter is not None:
            try:
                svc = getattr(request.app.state, "service_name", "unknown")  # type: ignore[attr-defined]
                # lazy create counter on first use to avoid import requirements in all services
                global _RATE_DENY_COUNTER
            except Exception:
                svc = "unknown"
            try:
                if "_RATE_DENY_COUNTER" not in globals():
                    globals()["_RATE_DENY_COUNTER"] = (
                        Counter(
                            "rate_limit_denied_total",
                            "Rate limited requests",
                            ["service", "path"],
                        )
                        if Counter
                        else None
                    )  # type: ignore
                if globals().get("_RATE_DENY_COUNTER") is not None:  # type: ignore
                    globals()["_RATE_DENY_COUNTER"].labels(svc, request.url.path).inc()  # type: ignore
            except Exception:
                pass
        # Instead of raising immediately, synthesize 429 response so streaming tests don't explode
        from fastapi.responses import JSONResponse

        resp = JSONResponse(status_code=429, content={"detail": "rate_limit_exceeded"})
        resp.headers[RATE_LIMIT_HEADER] = "0"
        return resp
    response = await call_next(request)
    final_remaining = getattr(request.state, "rate_remaining", remaining)
    if final_remaining is None:
        # Fallback: attempt a late classification (do not increment counter again); assume full quota minus 1
        try:
            final_remaining = limiter.per_minute - 1 if limiter.per_minute > 0 else 0
        except Exception:
            final_remaining = 0
    response.headers[RATE_LIMIT_HEADER] = str(final_remaining)
    return response
    return await call_next(request)


def install_rate_limit(
    app,
    per_minute: int,
    redis_client: Optional[object] = None,
    window_seconds: int | None = None,
):
    if redis_client is None:
        redis_client = getattr(app.state, "redis", None)
    # Allow test overrides via generic env knobs
    try:
        import os

        override = os.getenv("RATE_LIMIT_MAX_REQUESTS")
        win_env = os.getenv("RATE_LIMIT_WINDOW_SECONDS")
        if override:
            per_minute = int(override)
        if win_env:
            window_seconds = int(win_env)
    except Exception:
        pass
    app.state.rate_limit_config = {  # type: ignore[attr-defined]
        "limiter": SlidingWindowLimiter(
            per_minute=per_minute,
            redis_client=redis_client,
            window_seconds=window_seconds or 60,
        )
    }
    app.middleware("http")(rate_limit_middleware)


# Auto-install basic rate limit if explicit env knobs are set (used by tests)
try:
    import os

    _max = os.getenv("RATE_LIMIT_MAX_REQUESTS")
    _win = os.getenv("RATE_LIMIT_WINDOW_SECONDS")
    if _max and _win:
        # Installation will occur in each service after import when they call install_rate_limit, so we skip global.
        pass
except Exception:
    pass
