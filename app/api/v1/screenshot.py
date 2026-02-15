from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from app.api.dependencies import verify_api_key, limiter
from fastapi.requests import Request
from app.services.headless import headless_service
from app.schemas.screenshot import ScreenshotRequest
from app.utils.logger import logger
from typing import Annotated

router = APIRouter()

@router.get("/screenshot", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
async def get_screenshot(
    request: Request,
    url: Annotated[str, Query(max_length=2083)],
    full_page: bool = False,
    width: int = Query(1280, ge=320, le=3840),
    height: int = Query(720, ge=240, le=2160),
    delay: int = Query(0, ge=0, le=10000),
    dark_mode: bool = False
):
    """
    Capture a screenshot of a website.
    Returns a PNG image directly.
    """
    try:
        screenshot_bytes = await headless_service.take_screenshot(
            url=str(url),
            full_page=full_page,
            width=width,
            height=height,
            delay=delay,
            dark_mode=dark_mode
        )
        
        if not screenshot_bytes:
            raise HTTPException(status_code=500, detail="Failed to capture screenshot")
            
        return Response(content=screenshot_bytes, media_type="image/png")
        
    except Exception as e:
        logger.error("screenshot_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
