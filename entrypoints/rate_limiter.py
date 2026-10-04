import os
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi import Request, Response
from fastapi.responses import JSONResponse
    
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
)



def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    response = JSONResponse(
        {"error": "Rate limit exceeded"}, status_code=429
    )
    response = request.app.state.limiter._inject_headers(
        response, request.state.view_rate_limit
    )
    return response

@limiter.limit("100/minute")
def global_rate_limit(request: Request, response: Response):
    pass