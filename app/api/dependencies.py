from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.services.extract import ExtractService
from app.services.cache import cache_service
from app.services.fetcher import fetcher_service
from app.services.parser import parser_service
from app.services.headless import headless_service

limiter = Limiter(key_func=get_remote_address)

api_key_header = APIKeyHeader(name="X-RapidAPI-Proxy-Secret", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.X_RAPIDAPI_PROXY_SECRET:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

def get_extract_service():
    return ExtractService(cache_service, fetcher_service, parser_service, headless_service)
