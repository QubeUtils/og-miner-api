
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.extract import ExtractService
from app.schemas.metadata import ExtractRequest

@pytest.fixture
def mock_fetcher():
    return AsyncMock()

@pytest.fixture
def mock_headless():
    return AsyncMock()

@pytest.fixture
def mock_cache():
    m = AsyncMock()
    m.get.return_value = None
    return m

@pytest.fixture
def mock_parser():
    parser = MagicMock()
    parser.parse.return_value = {"title": "Test Title"}
    return parser

@pytest.fixture
def service(mock_cache, mock_fetcher, mock_parser, mock_headless):
    return ExtractService(mock_cache, mock_fetcher, mock_parser, mock_headless)

@pytest.mark.asyncio
async def test_standard_extract(service, mock_fetcher):
    mock_fetcher.fetch.return_value = "<html></html>"
    req = ExtractRequest(url="http://example.com")
    
    result = await service.extract_metadata(req)
    
    assert result["data"].title == "Test Title"
    mock_fetcher.fetch.assert_called_once()
    service.headless.fetch_and_render.assert_not_called()

@pytest.mark.asyncio
async def test_headless_extract(service, mock_headless):
    mock_headless.fetch_and_render.return_value = "<html></html>"
    req = ExtractRequest(url="http://example.com", enable_javascript=True)
    
    result = await service.extract_metadata(req)
    
    mock_headless.fetch_and_render.assert_called_once()
    service.fetcher.fetch.assert_not_called()

@pytest.mark.asyncio
async def test_geo_targeting(service, mock_fetcher):
    mock_fetcher.fetch.return_value = "<html></html>"
    req = ExtractRequest(url="http://example.com", country="US")
    
    await service.extract_metadata(req)
    
    args = mock_fetcher.fetch.call_args[1]
    assert args["country"] == "US"

@pytest.mark.asyncio
async def test_cookies(service, mock_fetcher):
    mock_fetcher.fetch.return_value = "<html></html>"
    cookies = {"session": "123"}
    req = ExtractRequest(url="http://example.com", cookies=cookies)
    
    await service.extract_metadata(req)
    
    args = mock_fetcher.fetch.call_args[1]
    assert args["cookies"] == cookies

@pytest.mark.asyncio
async def test_byop(service, mock_fetcher):
    mock_fetcher.fetch.return_value = "<html></html>"
    proxy = "http://user:pass@example.com:8080"
    req = ExtractRequest(url="http://example.com", proxy=proxy)
    
    # We need to patch validation since it checks network
    with patch("app.services.extract.validate_proxy_url") as mock_validate:
        await service.extract_metadata(req)
        mock_validate.assert_called_once_with(proxy)
    
    args = mock_fetcher.fetch.call_args[1]
    assert args["user_proxy"] == proxy

@pytest.mark.asyncio
async def test_invalid_byop_throws(service):
    req = ExtractRequest(url="http://example.com", proxy="http://localhost:3000")
    
    # Validation should raise ValueError
    with pytest.raises(ValueError):
         await service.extract_metadata(req)
