import time
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, BackgroundTasks, Request, HTTPException
from app.schemas.metadata import ExtractRequest, ExtractResponse, Metadata, MetaInfo
from app.services.cache import cache_service
from app.services.fetcher import fetcher_service
from app.services.parser import parser_service
from app.api.dependencies import limiter, verify_secret_header
from app.utils.logger import logger

router = APIRouter()

@router.post("/extract", response_model=ExtractResponse, dependencies=[Depends(verify_secret_header)])
@limiter.limit("60/minute")
async def extract_metadata(request: Request, body: ExtractRequest):
    start_time = time.time()
    url_str = str(body.url)
    domain = urlparse(url_str).netloc
    
    # Check cache
    if not body.force_refresh:
        cached_data = await cache_service.get(f"metadata:{url_str}")
        if cached_data:
            latency = (time.time() - start_time) * 1000
            logger.info("cache_hit", url=url_str, latency=latency)
            return ExtractResponse(
                meta=MetaInfo(url=url_str, domain=domain, latency_ms=latency),
                data=Metadata(**cached_data)
            )

    # Fetch and Parse
    try:
        html_content = None
        
        # 1. Try Headless if requested
        if body.enable_javascript:
            from app.services.headless import headless_service
            # Note: This might be slow. Client should be aware (timeout increased?)
            html_content = await headless_service.fetch_and_render(url_str)
            if html_content:
                logger.info("headless_fetch_success", url=url_str)
            else:
                logger.warning("headless_fetch_empty_fallback", url=url_str)
        
        # 2. Standard Fetch (Fallback or Default)
        if not html_content:
            html_content = await fetcher_service.fetch(url_str)

        metadata_dict = parser_service.parse(html_content, url_str)
        
        # oEmbed Fetching
        oembed_url = metadata_dict.pop("oembed_url", None)
        if oembed_url:
            # We treat oEmbed failure as non-critical
            oembed_data = await fetcher_service.fetch_json(oembed_url)
            if oembed_data:
                metadata_dict["oembed"] = oembed_data
        
        # Cache Result
        await cache_service.set(f"metadata:{url_str}", metadata_dict, ttl=86400)
        
        latency = (time.time() - start_time) * 1000
        logger.info("extraction_success", url=url_str, latency=latency, method="headless" if body.enable_javascript and html_content else "standard")
        
        return ExtractResponse(
            meta=MetaInfo(url=url_str, domain=domain, latency_ms=latency),
            data=Metadata(**metadata_dict)
        )
        
    except TimeoutError as e:
        latency = (time.time() - start_time) * 1000
        logger.error("fetch_timeout", url=url_str, latency=latency, error=str(e))
        raise HTTPException(status_code=504, detail={"error": "Request timed out", "code": "timeout", "message": str(e)})
        
    except ConnectionError as e:
        latency = (time.time() - start_time) * 1000
        logger.error("fetch_connection_error", url=url_str, latency=latency, error=str(e))
        raise HTTPException(status_code=502, detail={"error": "Failed to connect to upstream server", "code": "connection_error", "message": str(e)})

    except ValueError as e: # DNS/SSRF/HTTP Status
        latency = (time.time() - start_time) * 1000
        logger.error("fetch_value_error", url=url_str, latency=latency, error=str(e))
        raise HTTPException(status_code=400, detail={"error": "Invalid URL or Bad Request", "code": "invalid_request", "message": str(e)})
        
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        logger.error("extraction_failed", url=url_str, latency=latency, error=str(e))
        raise HTTPException(status_code=500, detail={"error": "Internal extraction failure", "code": "internal_error", "message": str(e)})
