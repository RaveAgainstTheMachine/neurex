import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("neurex.api.debug")

class DebugLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Incoming Request: {request.method} {request.url}")
        logger.info(f"Headers: {request.headers}")
        response = await call_next(request)
        logger.info(f"Response Status: {response.status_code}")
        return response
