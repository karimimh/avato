from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=(self)"
        storage_origin = ""
        parsed_storage = urlsplit(settings.s3_public_endpoint_url)
        if parsed_storage.scheme and parsed_storage.netloc:
            storage_origin = f" {parsed_storage.scheme}://{parsed_storage.netloc}"
        script_policy = "script-src 'self'"
        if settings.app_env == "development":
            script_policy += " 'unsafe-inline' 'unsafe-eval'"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            f"{script_policy}; "
            "style-src 'self' 'unsafe-inline'; "
            f"img-src 'self' blob: data:{storage_origin}; "
            f"media-src 'self' blob:{storage_origin}; "
            "connect-src 'self' ws: wss:; font-src 'self'; "
            "frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
        )
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis fixed-window limits at abuse-sensitive public boundaries."""

    def __init__(self, app: object) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    def rule(self, request: Request) -> tuple[int, int] | None:
        path = request.url.path
        if path.endswith(("/auth/register", "/auth/login")):
            return (10, 60)
        if "/audio" in path or "/media" in path:
            return (30, 60)
        if path.endswith("/exports") and request.method == "POST":
            return (10, 3600)
        return None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rule = self.rule(request)
        if rule:
            limit, window = rule
            identity = request.client.host if request.client else "unknown"
            digest = hashlib.sha256(identity.encode()).hexdigest()[:24]
            bucket = int(time.time()) // window
            key = f"rate:{digest}:{request.url.path}:{bucket}"
            try:
                count = await self.redis.incr(key)
                if count == 1:
                    await self.redis.expire(key, window + 2)
                if count > limit:
                    return JSONResponse(
                        {
                            "error": {
                                "code": "rate_limited",
                                "message": "کمی صبر کنید و دوباره تلاش کنید.",
                                "details": {},
                            }
                        },
                        status_code=429,
                        headers={"Retry-After": str(window)},
                    )
            except Exception:
                logger.warning("rate_limit_store_unavailable", exc_info=True)
        return await call_next(request)
