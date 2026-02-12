from playwright.async_api import async_playwright
from app.utils.logger import logger

class HeadlessFetcher:
    async def fetch_and_render(self, url: str) -> str | None:
        """
        Launches a headless browser, navigates to the URL, checks for specific
        security risks (optional), waits for network idle, and returns specific content.
        
        Note: This is resource intensive. Should only be used as a fallback or if requested.
        """
        async with async_playwright() as p:
            # Launch configs: disable sandboxing for docker, etc.
            # In a real heavy env, we might want to connect to a remote browser instance.
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox'] # Docker requires this in some environments
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            try:
                # Basic protection: blocking resource types that are unnecessary for metadata
                await page.route("**/*", lambda route: route.continue_() if route.request.resource_type in ["document", "script", "xhr", "fetch"] else route.abort())

                response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                if not response:
                    return None
                    
                # Wait for some JS execution if needed, e.g. network idle for 1s
                # await page.wait_for_load_state("networkidle") 
                # ^ Networkidle can be flaky on some sites with continuous polling. 
                # DOMContentLoaded is safer for initial paint.
                
                # Get rendered HTML
                content = await page.content()
                return content
                
            except Exception as e:
                logger.error("headless_fetch_failed", url=url, error=str(e))
                return None
            finally:
                await browser.close()

headless_service = HeadlessFetcher()
