from playwright.async_api import async_playwright
from app.utils.logger import logger

from app.core.config import settings

class HeadlessFetcher:
    def _get_launch_options(self):
        options = {
            "headless": True,
            "args": ['--no-sandbox', '--disable-setuid-sandbox']
        }
        if settings.PROXY_URL:
            options["proxy"] = {"server": settings.PROXY_URL}
        return options

    async def fetch_and_render(self, url: str) -> str | None:
        """
        Launches a headless browser, navigates to the URL, checks for specific
        security risks (optional), waits for network idle, and returns specific content.
        
        Note: This is resource intensive. Should only be used as a fallback or if requested.
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(**self._get_launch_options())
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                page = await context.new_page()
                
                try:
                    # Basic protection: blocking resource types that are unnecessary for metadata
                    await page.route("**/*", lambda route: route.continue_() if route.request.resource_type in ["document", "script", "xhr", "fetch"] else route.abort())

                    response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    if not response:
                        await browser.close()
                        return None
                        
                    # Wait for some JS execution if needed, e.g. network idle for 1s
                    # await page.wait_for_load_state("networkidle") 
                    # ^ Networkidle can be flaky on some sites with continuous polling. 
                    # DOMContentLoaded is safer for initial paint.
                    
                    # Get rendered HTML
                    content = await page.content()
                    await browser.close()
                    return content
                    
                except Exception as e:
                    await browser.close()
                    return None
                    
        except Exception as e:
            logger.error("headless_service_init_failed", url=url, error=str(e))
            return None

    async def take_screenshot(self, url: str, full_page: bool = False, width: int = 1280, height: int = 720, delay: int = 0, dark_mode: bool = False) -> bytes | None:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(**self._get_launch_options())
                
                color_scheme = "dark" if dark_mode else "light"
                context = await browser.new_context(
                    viewport={"width": width, "height": height},
                    color_scheme=color_scheme,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                page = await context.new_page()
                
                try:
                    # Allow images for screenshots!
                    await page.route("**/*", lambda route: route.continue_())
                    
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    
                    if delay > 0:
                        await page.wait_for_timeout(delay)
                    else:
                        try:
                            await page.wait_for_load_state("networkidle", timeout=3000)
                        except:
                            pass
                    
                    screenshot = await page.screenshot(full_page=full_page, type="png")
                    await browser.close()
                    return screenshot
                    
                except Exception as e:
                    logger.error("screenshot_failed", url=url, error=str(e))
                    await browser.close()
                    return None
                    
        except Exception as e:
            logger.error("headless_service_init_failed", url=url, error=str(e))
            return None

headless_service = HeadlessFetcher()
