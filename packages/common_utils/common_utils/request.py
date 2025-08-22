import uuid
from typing import Callable, Awaitable
from fastapi import Request, Response

REQUEST_ID_HEADER = "X-Request-ID"


async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
):
    """Lightweight middleware that ensures a request id exists and is propagated via headers and request.state.
    Logging & metrics are intentionally left to service-specific middleware so logs aren't duplicated."""
    req_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
    request.state.request_id = req_id  # type: ignore[attr-defined]
    response = await call_next(request)
    response.headers.setdefault(REQUEST_ID_HEADER, req_id)
    return response


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None) or request.headers.get(
        REQUEST_ID_HEADER
    )
