
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import BackgroundTasks
from app.api.v1.batch import process_batch
from app.schemas.batch import BatchExtractRequest
from app.schemas.metadata import ExtractResponse, MetaInfo, Metadata

@pytest.mark.asyncio
async def test_batch_all_success():
    mock_service = AsyncMock()
    # Mock return must match what extract_metadata service returns (dict)
    mock_service.extract_metadata.return_value = {
        "meta": MetaInfo(url="http://ok.com", domain="ok.com", latency_ms=10),
        "data": Metadata(title="OK")
    }
    
    req = BatchExtractRequest(urls=["http://ok.com"])
    
    response = await process_batch(req, BackgroundTasks(), extract_service=mock_service)
    
    assert response.total == 1
    assert response.successful == 1
    assert response.failed == 0
    assert response.results["http://ok.com/"].data.title == "OK"

@pytest.mark.asyncio
async def test_batch_partial_failure():
    mock_service = AsyncMock()
    
    async def side_effect(request):
        if "fail.com" in str(request.url):
            raise Exception("Boom")
        return {
            "meta": MetaInfo(url="http://ok.com", domain="ok.com", latency_ms=10),
            "data": Metadata(title="OK")
        }
    
    mock_service.extract_metadata.side_effect = side_effect
    
    req = BatchExtractRequest(urls=["http://ok.com", "http://fail.com"])
    
    response = await process_batch(req, BackgroundTasks(), extract_service=mock_service)
    
    assert response.total == 2
    assert response.successful == 1
    assert response.failed == 1
    
    # Verify results order matches (asyncio.gather returns in order)
    assert response.results["http://ok.com/"].meta.url == "http://ok.com"
    
    assert response.results["http://fail.com/"].get("success") is False
    assert "Boom" in response.results["http://fail.com/"]["error"]
