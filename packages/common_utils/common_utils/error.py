from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import traceback
from typing import Any, Dict

STANDARD_ERROR_VERSION = 1


def _base_payload(code: str, message: str, request_id: str | None, details: Any = None) -> Dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
            "ts": datetime.utcnow().isoformat() + "Z",
            "ver": STANDARD_ERROR_VERSION,
        }
    }


def install_error_handlers(app, include_server_stack: bool = False):
    """Register consistent JSON error handlers for HTTPException & generic Exception.

    include_server_stack: if True, include traceback in 'details.stack' (avoid in production).
    """

    @app.exception_handler(HTTPException)
    async def _http_exc_handler(request: Request, exc: HTTPException):  # type: ignore
        rid = getattr(request.state, "request_id", None)
        payload = _base_payload(
            code=str(exc.status_code),
            message=exc.detail if isinstance(exc.detail, str) else "http_error",
            request_id=rid,
            details=exc.detail if isinstance(exc.detail, dict) else None,
        )
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(Exception)
    async def _unhandled_exc_handler(request: Request, exc: Exception):  # type: ignore
        rid = getattr(request.state, "request_id", None)
        details = {}
        if include_server_stack:
            details["stack"] = traceback.format_exc().splitlines()[-8:]
            details["type"] = exc.__class__.__name__
        payload = _base_payload(
            code="internal_error", message="internal server error", request_id=rid, details=details or None
        )
        return JSONResponse(status_code=500, content=payload)

    # Expose for later inspection/testing
    app.state.error_handler_installed = True  # type: ignore
    return app
