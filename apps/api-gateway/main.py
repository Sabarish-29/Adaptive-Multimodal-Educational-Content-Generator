"""Minimal FastAPI gateway to unify service access under single origin.

Run (dev):
    uvicorn apps.api-gateway.main:app --reload --port 9000
Then set FRONTEND to call http://localhost:9000/api/... instead of direct service ports.
"""
import os, sys
from pathlib import Path
from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Make shared packages importable without requiring external PYTHONPATH exports
try:  # best-effort; non-fatal if anything fails
        root = Path(__file__).resolve().parents[2]
        pkg_dir = root / "packages"
        if pkg_dir.exists():
                p = str(pkg_dir)
                if p not in sys.path:
                        sys.path.insert(0, p)
except Exception:
        pass

# Target service base URLs (env override capable)
ADAPT_URL = os.getenv("ADAPT_URL", "http://localhost:8001")
SESSIONS_URL = os.getenv("SESSIONS_URL", "http://localhost:8002")
CONTENT_URL = os.getenv("CONTENT_URL", "http://localhost:8003")
PROFILES_URL = os.getenv("PROFILES_URL", "http://localhost:8000")
RECOMMENDATIONS_URL = os.getenv("RECOMMENDATIONS_URL", "http://localhost:8090")
RECOMMENDATIONS_ENABLED = os.getenv("RECOMMENDATIONS_ENABLED", "false").strip().lower() in {"1","true","yes","on"}
ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://localhost:8008")
RAG_URL = os.getenv("RAG_URL", "http://localhost:8005")

app = FastAPI(title="Adaptive API Gateway", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple proxy helper that strips a specific prefix (e.g. /api/sessions)
def _build_target_url(request: Request, target_base: str, prefix: str) -> str:
    raw_path = request.url.path
    if raw_path.startswith(prefix):
        path_suffix = raw_path[len(prefix):]
    else:
        # fallback: previous behavior (remove only /api) — avoids total breakage if mis-routed
        path_suffix = raw_path.replace("/api", "", 1)
    if not path_suffix:
        path_suffix = "/"
    return target_base.rstrip('/') + path_suffix

async def _proxy(request: Request, target_base: str, prefix: str):
    target_url = _build_target_url(request, target_base, prefix)
    method = request.method.lower()
    headers = dict(request.headers)
    headers.pop("host", None)
    accept = headers.get("accept", "").lower()
    is_sse = "text/event-stream" in accept or target_url.endswith("/live")
    if is_sse and method == "get":
        try:
            try:
                print(f"[gateway][sse] START stream -> {target_url}")
            except Exception:
                pass
            client = httpx.AsyncClient(follow_redirects=True, timeout=None)
            upstream_req = client.build_request(method, target_url, headers=headers, params=request.query_params)
            upstream_resp = await client.send(upstream_req, stream=True)
        except httpx.RequestError as e:
            # Upstream is unreachable or errored; return a clean 502 instead of crashing the gateway
            try:
                await client.aclose()
            except Exception:
                pass
            detail = {"error": "upstream_unreachable", "target": target_url, "reason": str(e)}
            return JSONResponse(status_code=502, content=detail)
        try:
            sample_headers = {k: upstream_resp.headers[k] for k in list(upstream_resp.headers)[:8]}
            print(f"[gateway][sse] upstream {upstream_resp.status_code} {target_url} headers: {sample_headers}")
        except Exception:
            pass

        async def event_stream():
            chunk_count = 0
            try:
                async for text_chunk in upstream_resp.aiter_text():
                    if not text_chunk:
                        continue
                    chunk_count += 1
                    if chunk_count <= 5:
                        try:
                            preview = text_chunk[:100].replace('\n', ' ')[:100]
                            print(f"[gateway][sse] text-chunk#{chunk_count} chars={len(text_chunk)} preview={preview!r}")
                        except Exception:
                            pass
                    # Pass through exactly as received
                    yield text_chunk.encode('utf-8')
            finally:
                try:
                    await upstream_resp.aclose()
                finally:
                    await client.aclose()

        out_headers = {k: v for k, v in upstream_resp.headers.items() if k.lower() not in {"content-length"}}
        out_headers.pop("Content-Length", None)
        out_headers["Cache-Control"] = out_headers.get("Cache-Control", "no-cache")
        out_headers["X-Target-Url"] = target_url
        return StreamingResponse(event_stream(), status_code=upstream_resp.status_code, headers=out_headers, media_type="text/event-stream")
    # Non-SSE (default) path buffers body
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        data = await request.body()
        try:
            print(f"[gateway][proxy] {request.method} {target_url} (sse={is_sse})")
        except Exception:
            pass
        try:
            resp = await client.request(method, target_url, content=data, headers=headers, params=request.query_params)
        except httpx.RequestError as e:
            # Surface a 502 Bad Gateway with context when the upstream cannot be reached
            detail = {"error": "upstream_unreachable", "target": target_url, "reason": str(e)}
            return JSONResponse(status_code=502, content=detail)
    out_headers = {k: v for k, v in resp.headers.items() if k.lower() not in {"transfer-encoding"}}
    out_headers["X-Target-Url"] = target_url
    return Response(content=resp.content, status_code=resp.status_code, headers=out_headers, media_type=resp.headers.get("content-type"))

sessions_router = APIRouter()

@sessions_router.get("/")
async def sessions_root():
    return {
        "service": "sessions",
        "description": "Base path for sessions service via gateway proxy.",
        "endpoints": [
            "/api/sessions/healthz",
            "/api/sessions/v1/sessions (POST create, GET list if implemented)",
            "/api/sessions/v1/sessions/{session_id}/live (GET SSE)",
        ],
    }

@sessions_router.api_route("/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def sessions_proxy(path: str, request: Request):  # noqa: D401
    return await _proxy(request, SESSIONS_URL, "/api/sessions")

# Lightweight stub for SSE live endpoint when upstream isn't ready yet.
@app.get("/api/sessions/v1/sessions/{session_id}/live")
async def sessions_live_stub(session_id: str):
    async def gen():
        # Emit a small heartbeat stream so the UI doesn't error out.
        yield b": keep-alive\n\n"
        yield b"event: recommendation\n"
        yield b"data: {\"cached\":true,\"id\":\"warmup\",\"strategy\":\"explore\"}\n\n"
    headers = {"Cache-Control":"no-cache", "X-Stub":"true"}
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)

app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
@app.api_route("/api/adaptation/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def adaptation_proxy(path: str, request: Request):
    return await _proxy(request, ADAPT_URL, "/api/adaptation")

@app.api_route("/api/content/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def content_proxy(path: str, request: Request):
    return await _proxy(request, CONTENT_URL, "/api/content")

@app.api_route("/api/profiles/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def profiles_proxy(path: str, request: Request):
    return await _proxy(request, PROFILES_URL, "/api/profiles")

@app.get("/api/status")
async def status_aggregate():
    # Keep it simple; detailed pings can be added later.
    return {"ok": True, "services": ["profiles","sessions","analytics","content","adaptation","rag"]}

if not RECOMMENDATIONS_ENABLED or not RECOMMENDATIONS_URL:
    recs_router = APIRouter()

    @recs_router.get("/healthz")
    async def recs_healthz():
        return {"status": "ok", "enabled": False, "reason": "recommendations_disabled"}

    @recs_router.get("/status")
    async def recs_status():
        return {"enabled": False}

    @recs_router.api_route("/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
    async def recs_disabled_catchall(path: str, request: Request):
        # Return 200 with a disabled payload to avoid noisy UI error toasts
        return JSONResponse(status_code=200, content={"enabled": False, "note": "recommendations disabled"})

    app.include_router(recs_router, prefix="/api/recommendations", tags=["recommendations"])
else:
    @app.api_route("/api/recommendations/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
    async def recs_proxy(path: str, request: Request):
        return await _proxy(request, RECOMMENDATIONS_URL, "/api/recommendations")

@app.api_route("/api/analytics/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def analytics_proxy(path: str, request: Request):
    return await _proxy(request, ANALYTICS_URL, "/api/analytics")

@app.api_route("/api/rag/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def rag_proxy(path: str, request: Request):
    return await _proxy(request, RAG_URL, "/api/rag")

@app.get("/healthz")
async def health():
    return {"status": "ok", "gateway": True}
