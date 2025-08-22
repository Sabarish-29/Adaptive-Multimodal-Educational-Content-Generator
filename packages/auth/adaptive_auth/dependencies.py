import os
import time
import jwt
from fastapi import Header, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Callable

MOCK_PUBLIC_KEY = os.getenv("MOCK_PUBLIC_KEY", "mock-public-key")
ALGO = os.getenv("JWT_ALGO", "HS256")  # For mock use symmetric; production RS256
ISSUER = os.getenv("JWT_ISSUER", "adaptive-edu")


class UserContext(BaseModel):
    sub: str
    roles: List[str]
    tenant_id: Optional[str] = None
    exp: Optional[int] = None


class RoleRequirement:
    def __init__(self, allowed: List[str]):
        self.allowed = allowed

    def __call__(self, user: UserContext):
        if not any(r in self.allowed for r in user.roles):
            raise HTTPException(status_code=403, detail="insufficient_role")


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> UserContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_token")
    token = authorization.split()[1]
    try:
        payload = jwt.decode(
            token,
            MOCK_PUBLIC_KEY,
            algorithms=[ALGO],
            options={"verify_signature": ALGO != "none"},
            issuer=ISSUER,
            options_override={},
        )
    except Exception as e:
        # For mock, allow unsigned tokens when ALGO=none
        try:
            if ALGO == "none":
                payload = jwt.decode(token, options={"verify_signature": False})
            else:
                raise
        except Exception:
            raise HTTPException(status_code=401, detail="invalid_token") from e
    roles = payload.get("roles", [])
    ctx = UserContext(
        sub=payload.get("sub", "unknown"),
        roles=roles,
        tenant_id=payload.get("tenant_id"),
        exp=payload.get("exp"),
    )
    if ctx.exp and ctx.exp < time.time():
        raise HTTPException(status_code=401, detail="token_expired")
    return ctx


def require_roles(*roles: str) -> Callable:
    def dep(user: UserContext = Depends(get_current_user)):
        if not any(r in user.roles for r in roles):
            raise HTTPException(status_code=403, detail="forbidden")
        return user

    return dep
