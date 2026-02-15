
import pytest
from unittest.mock import AsyncMock, patch
from app.services.headless import headless_service

@pytest.mark.asyncio
async def test_headless_fetch_success():
    # Patch async_playwright where it is USED
    with patch("app.services.headless.async_playwright") as mock_ap:
        # Setup mock chain
        mock_context_manager = AsyncMock()
        mock_ap.return_value = mock_context_manager
        
        mock_p = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_p
        
        mock_browser = AsyncMock()
        mock_p.chromium.launch.return_value = mock_browser
        
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_page = AsyncMock()
        # Mock new_page to return our mock page
        mock_context.new_page.return_value = mock_page
        
        # Mock goto response
        mock_response = AsyncMock()
        mock_page.goto.return_value = mock_response
        
        # Mock content
        mock_page.content.return_value = "<html><title>Headless Success</title></html>"
        
        # Execution
        content = await headless_service.fetch_and_render("https://spa-example.com")
        
        # Assertions
        assert content == "<html><title>Headless Success</title></html>"
        mock_page.goto.assert_called()

@pytest.mark.asyncio
async def test_headless_fetch_error():
     with patch("app.services.headless.async_playwright") as mock_ap:
        mock_context_manager = AsyncMock()
        mock_ap.return_value = mock_context_manager
        mock_context_manager.__aenter__.side_effect = Exception("Browser crashed")
        
        content = await headless_service.fetch_and_render("https://crash.com")
        assert content is None
