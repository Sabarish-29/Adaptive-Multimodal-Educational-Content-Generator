"""Common error handling utilities for FastAPI services.

Provides an install_error_handlers(app) helper that registers JSON
handlers for HTTPException and generic Exception, adding request id if present.
"""
from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

REQUEST_ID_HEADER = "X-Request-ID"


def _extract_request_id(request: Request):  # best-effort
    rid = None
    try:
        rid = getattr(request.state, "request_id", None) or request.headers.get(REQUEST_ID_HEADER)
    except Exception:
        pass
    return rid


def install_error_handlers(app: FastAPI) -> None:
    """Register simple JSON exception handlers (idempotent)."""
    if getattr(app.state, "_error_handlers_installed", False):
        return

    @app.exception_handler(HTTPException)
    async def _http_exc_handler(request: Request, exc: HTTPException):  # type: ignore
        rid = _extract_request_id(request)
        payload = {"detail": exc.detail, "status": exc.status_code}
        if rid:
            payload["request_id"] = rid
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(Exception)
    async def _generic_exc_handler(request: Request, exc: Exception):  # type: ignore
        rid = _extract_request_id(request)
        payload = {"detail": "internal_error", "type": exc.__class__.__name__}
        if rid:
            payload["request_id"] = rid
        return JSONResponse(status_code=500, content=payload)

    setattr(app.state, "_error_handlers_installed", True)

__all__ = ["install_error_handlers"]
