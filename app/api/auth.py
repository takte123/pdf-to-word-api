"""
API Key authentication middleware
"""

from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging import logger

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key on all protected routes"""

    async def dispatch(self, request: Request, call_next):
        # Skip auth for health endpoint
        if request.url.path == "/health":
            return await call_next(request)

        # Skip auth for docs
        if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Validate API key
        settings = get_settings()
        api_key = request.headers.get("X-API-Key")
        client_ip = request.client.host if request.client else "unknown"

        if not api_key:
            logger.warning(f"API key missing - IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key header missing",
            )

        if api_key != settings.api_key:
            logger.warning(f"Invalid API key - IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key"
            )

        return await call_next(request)


async def verify_api_key(request: Request) -> str:
    """Dependency to verify API key"""
    settings = get_settings()
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key header missing"
        )

    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key"
        )

    return api_key
