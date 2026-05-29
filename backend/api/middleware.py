"""
Security Middlewares for SOC Platform.
Includes Rate Limiting to prevent DDoS and API abuse.
"""
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding window rate limiter."""
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = {}

    async def dispatch(self, request: Request, call_next):
        # Ignore websockets and health endpoints
        if request.scope["type"] == "websocket" or request.url.path in ["/"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old requests
        if client_ip in self.clients:
            self.clients[client_ip] = [t for t in self.clients[client_ip] if now - t < self.window_seconds]
        else:
            self.clients[client_ip] = []

        # Check limit
        if len(self.clients[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests. Please slow down."}
            )

        self.clients[client_ip].append(now)
        response = await call_next(request)
        return response
