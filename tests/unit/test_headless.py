import sys
from unittest.mock import MagicMock, AsyncMock

# 1. Mock the missing playwright module BEFORE importing the service
mock_pw = MagicMock()
mock_async_api = MagicMock()
sys.modules["playwright"] = mock_pw
sys.modules["playwright.async_api"] = mock_async_api

# Mock the async_playwright function
mock_context_manager = AsyncMock()
mock_async_api.async_playwright = converter = MagicMock(return_value=mock_context_manager)

# 2. Now import the service (which thinks playwright is installed)
# We need to use importlib to reload if it was already imported (unlikely in fresh run but good practice)
import app.services.headless
from app.services.headless import headless_service
import pytest

@pytest.mark.asyncio
async def test_headless_fetch_success():
    # Setup the mock chain for the context manager: async with async_playwright() as p:
    mock_p = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_p
    
    mock_browser = AsyncMock()
    mock_p.chromium.launch.return_value = mock_browser
    
    mock_context = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    
    mock_page = AsyncMock()
    mock_context.new_page.return_value = mock_page
    
    mock_response = AsyncMock()
    mock_page.goto.return_value = mock_response
    mock_page.content.return_value = "<html><title>Headless Success</title></html>"

    # Execution
    content = await headless_service.fetch_and_render("https://spa-example.com")
    
    # Assertions
    assert content == "<html><title>Headless Success</title></html>"
    mock_page.goto.assert_called_with("https://spa-example.com", wait_until="domcontentloaded", timeout=15000)

@pytest.mark.asyncio
async def test_headless_fetch_error():
    # Simulate crash
    mock_context_manager.__aenter__.side_effect = Exception("Browser crashed")
    
    content = await headless_service.fetch_and_render("https://crash.com")
    assert content is None
