from fastapi import Security, HTTPException, Request
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings

limiter = Limiter(key_func=get_remote_address)

api_key_header = APIKeyHeader(
    name="X-RapidAPI-Proxy-Secret", 
    auto_error=False, 
    description="Secret key to verify requests coming from RapidAPI (or direct access if you have the secret)."
)

async def verify_secret_header(api_key: str = Security(api_key_header)):
    if api_key != settings.X_RAPIDAPI_PROXY_SECRET:
        raise HTTPException(status_code=403, detail="Invalid Secret Header")
