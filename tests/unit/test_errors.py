import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.fetcher import fetcher_service

client = TestClient(app)

# Mock config to bypass secret header if needed, or just pass it in requests
HEADERS = {"X-RapidAPI-Proxy-Secret": "dev_proxy_secret"}

@pytest.fixture(autouse=True)
def mock_redis():
    with patch("app.services.cache.cache_service.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        yield mock_get

@pytest.mark.asyncio
async def test_fetch_timeout_handling():
    with patch.object(fetcher_service.client, 'stream', side_effect=httpx.TimeoutException("Mock Timeout")):
        response = client.post("/v1/extract", json={"url": "https://timeout.com"}, headers=HEADERS)
        assert response.status_code == 504
        assert response.json()["detail"]["code"] == "timeout"

@pytest.mark.asyncio
async def test_fetch_connection_error_handling():
    with patch.object(fetcher_service.client, 'stream', side_effect=httpx.ConnectError("Mock Connection Error")):
        response = client.post("/v1/extract", json={"url": "https://down.com"}, headers=HEADERS)
        assert response.status_code == 502
        assert response.json()["detail"]["code"] == "connection_error"

@pytest.mark.asyncio
async def test_fetch_ssrf_error_handling():
    # SSRF is raised as ValueError in fetcher service before stream
    response = client.post("/v1/extract", json={"url": "http://127.0.0.1"}, headers=HEADERS)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_request"
