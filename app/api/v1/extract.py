import time
import httpx
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, Request, HTTPException
from app.schemas.metadata import ExtractRequest, ExtractResponse
from app.services.extract import ExtractService
from app.api.dependencies import limiter, verify_api_key, get_extract_service
from app.utils.logger import logger

router = APIRouter()

@router.post("/extract", response_model=ExtractResponse, operation_id="extract_metadata", summary="Extract Metadata")
@limiter.limit("60/minute")
async def extract_metadata(
    request: Request, 
    body: ExtractRequest,
    api_key: str = Depends(verify_api_key),
    extract_service: ExtractService = Depends(get_extract_service)
):
    try:
        # Service returns dict, Pydantic model validates it
        result = await extract_service.extract_metadata(body)
        return ExtractResponse(**result)
        
    except httpx.TimeoutException as e:
        logger.error("fetch_timeout", url=str(body.url), error=str(e))
        raise HTTPException(status_code=504, detail={"error": "Request timed out", "code": "timeout", "message": str(e)})
        
    except httpx.RequestError as e:
        logger.error("fetch_connection_error", url=str(body.url), error=str(e))
        raise HTTPException(status_code=502, detail={"error": "Failed to connect to upstream server", "code": "connection_error", "message": str(e)})
        
    except ValueError as e: # DNS/SSRF/HTTP Status
        logger.error("fetch_value_error", url=str(body.url), error=str(e))
        raise HTTPException(status_code=400, detail={"error": "Invalid URL or Bad Request", "code": "invalid_request", "message": str(e)})
        
    except Exception as e:
        logger.error("extraction_failed", url=str(body.url), error=str(e))
        raise HTTPException(status_code=500, detail={"error": "Internal extraction failure", "code": "internal_error", "message": str(e)})
