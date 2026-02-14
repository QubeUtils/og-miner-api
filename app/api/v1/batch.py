import asyncio
from fastapi import APIRouter, Depends, BackgroundTasks
from typing import List

from app.schemas.batch import BatchExtractRequest, BatchExtractResponse
from app.schemas.metadata import ExtractRequest
from app.api.dependencies import verify_api_key, get_extract_service
from app.services.extract import ExtractService
from app.utils.logger import logger

router = APIRouter()

@router.post("/batch/extract", response_model=BatchExtractResponse)
async def batch_extract_metadata(
    request: BatchExtractRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
    extract_service: ExtractService = Depends(get_extract_service)
):
    """
    Extract metadata for multiple URLs in parallel.
    """
    logger.info("batch_extract_request", count=len(request.urls))
    
    async def process_url(url: str):
        try:
            # Create individual request object
            single_request = ExtractRequest(
                url=str(url),
                enable_javascript=request.enable_javascript,
                force_refresh=request.force_refresh
            )
            # Re-use the existing extraction service logic
            result = await extract_service.extract_metadata(single_request)
            return str(url), result
        except Exception as e:
            logger.error("batch_item_failed", url=str(url), error=str(e))
            return str(url), {"error": str(e), "success": False}

    # Run all tasks in parallel
    tasks = [process_url(url) for url in request.urls]
    results_list = await asyncio.gather(*tasks)
    
    # Aggregate results
    results_map = {url: res for url, res in results_list}
    
    successful = sum(1 for res in results_map.values() if not isinstance(res, dict) or res.get("success", True))
    failed = len(request.urls) - successful

    return BatchExtractResponse(
        results=results_map,
        total=len(request.urls),
        successful=successful,
        failed=failed
    )
