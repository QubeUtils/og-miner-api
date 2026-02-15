from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.utils.logger import setup_logging, logger
from app.api.v1 import extract, screenshot, batch, image
from app.api.dependencies import limiter
from app.services.cache import cache_service
from app.services.fetcher import fetcher_service

from app.services.proxy_manager import proxy_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        setup_logging()
        logger.info("startup")
        await proxy_manager.initialize()
        
        if settings.X_RAPIDAPI_PROXY_SECRET == "MISSING_SECRET":
            logger.error("startup_error", message="X_RAPIDAPI_PROXY_SECRET is not set! Authentication will fail or be insecure.")
            
        yield
    except Exception as e:
        # Fallback logging if structlog fails or other startup error
        import sys
        print(f"CRITICAL STARTUP ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise e
        
    # Shutdown
    await cache_service.close()
    await fetcher_service.close()
    logger.info("shutdown")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    contact=settings.CONTACT,
    lifespan=lifespan
)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to OG Miner API", "docs": "/docs"}

app.include_router(extract.router, prefix="/v1", tags=["extract"])
app.include_router(screenshot.router, prefix="/v1", tags=["screenshot"])
app.include_router(batch.router, prefix="/v1", tags=["batch"])
app.include_router(image.router, prefix="/v1", tags=["image"])

# Health Check
@app.get("/health", include_in_schema=False)
async def health_check():
    redis_status = await cache_service.ping()
    return {
        "status": "ok" if redis_status else "degraded",
        "redis": "connected" if redis_status else "disconnected"
    }

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Failed to extract", "code": "extraction_error"}
    )
