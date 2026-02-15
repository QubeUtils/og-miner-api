from fastapi import APIRouter, HTTPException, Query, Response
import base64
from typing import Optional

from app.services.image_proxy import image_proxy_service
from app.services.cache import cache_service
from app.utils.logger import logger

router = APIRouter()

@router.get("/image", operation_id="image_proxy", summary="Image Proxy")
async def proxy_image(
    url: str = Query(..., description="The URL of the image to proxy"),
    width: Optional[int] = Query(None, gt=0, le=2000, description="Target width"),
    height: Optional[int] = Query(None, gt=0, le=2000, description="Target height")
):
    """
    Proxies and optionally resizes an image. 
    Results are cached for performance.
    Returns WebP format by default.
    """
    # Cache Key Generation
    cache_key = f"img:{url}:w{width or 'orig'}:h{height or 'orig'}"
    
    # Check Cache
    # Check Cache (Base64 Encoded)
    try:
        cached_data = await cache_service.redis.get(cache_key)
        if cached_data:
            image_bytes = base64.b64decode(cached_data)
            logger.info("cache_hit_image", url=url)
            return Response(content=image_bytes, media_type="image/webp")
    except Exception as e:
        logger.warning("image_cache_read_error", error=str(e))

    try:
        # Fetch
        image_bytes = await image_proxy_service.fetch_image(url)
        if not image_bytes:
            raise HTTPException(status_code=404, detail="Image not found or inaccessible")
            
        # Process
        processed_bytes, media_type = image_proxy_service.process_image(image_bytes, width, height)
        
        # Save to Cache (Base64 Encoded)
        try:
            b64_data = base64.b64encode(processed_bytes).decode('utf-8')
            await cache_service.redis.set(cache_key, b64_data, ex=86400) # 24h TTL
        except Exception as e:
            logger.error("image_cache_write_error", error=str(e))
        
        # Return Response
        return Response(content=processed_bytes, media_type=media_type)
        
    except Exception as e:
        logger.error("image_proxy_endpoint_error", url=url, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process image")
