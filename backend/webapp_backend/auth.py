"""Authentication helpers (stub) for the backend.

Replaces simple x-api-key check with bearer token validation so the frontend
can supply Authorization: Bearer demo-token. In real deployments, integrate
OIDC/JWT verification here.
"""

import logging
import os

from fastapi import HTTPException, Request

logger = logging.getLogger("webapp_backend.auth")

EXPECTED_TOKEN: str = os.getenv("WEBAPP_DEMO_TOKEN", "demo-token")
DISABLE_AUTH: bool = os.getenv("WEBAPP_DISABLE_AUTH", "").lower() in {
    "1",
    "true",
    "yes",
}


async def require_auth(request: Request) -> None:
    """Validate the incoming request contains the expected bearer token.

    Accepts either:
    - Authorization: Bearer demo-token
    - X-API-Key: demo-token (legacy fallback)

    To disable auth temporarily set environment variable WEBAPP_DISABLE_AUTH=1.
    """
    if DISABLE_AUTH:
        logger.warning(
            "Auth disabled via WEBAPP_DISABLE_AUTH; permitting all requests.",
        )
        return

    auth_header = request.headers.get("authorization") or ""
    token: str | None = None
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    else:
        # Fallback legacy header
        token = request.headers.get("x-api-key")

    # Allow token passed via query parameter for SSE GET endpoints
    # where setting custom headers may be difficult (e.g., plain EventSource).
    if not token:
        token = request.query_params.get("token")

    if token != EXPECTED_TOKEN:
        logger.info(
            "Unauthorized request: provided_token_prefix=%s expected_token=%s path=%s",
            (token or "")[:6],
            EXPECTED_TOKEN,
            request.url.path,
        )
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.debug("Auth succeeded for path %s", request.url.path)


def get_current_user() -> str:
    """Return a stub user id after auth passes."""
    return "user_demo"
