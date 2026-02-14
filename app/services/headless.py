from playwright.async_api import async_playwright
from app.utils.logger import logger

from app.services.proxy_manager import proxy_manager

class HeadlessFetcher:
    def _get_launch_options(self, proxy_url: str | None = None):
        options = {
            "headless": True,
            "args": ['--no-sandbox', '--disable-setuid-sandbox']
        }
        if proxy_url:
            options["proxy"] = {"server": proxy_url}
        return options

    async def fetch_and_render(self, url: str) -> str | None:
        """
        Launches a headless browser... with retries for proxies.
        """
        retries = 3
        for attempt in range(retries):
            proxy = await proxy_manager.get_proxy()
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(**self._get_launch_options(proxy))
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    
                    page = await context.new_page()
                    
                    try:
                        await page.route("**/*", lambda route: route.continue_() if route.request.resource_type in ["document", "script", "xhr", "fetch"] else route.abort())

                        response = await page.goto(url, wait_until="domcontentloaded", timeout=20000) # Increased timeout for proxy latency
                        if not response:
                            await browser.close()
                            return None
                        
                        content = await page.content()
                        await browser.close()
                        return content
                        
                    except Exception as e:
                        await browser.close()
                        raise e # Re-raise to trigger retry loop
                        
            except Exception as e:
                logger.warning("headless_retry", url=url, attempt=attempt+1, error=str(e), proxy=proxy)
                if proxy:
                    await proxy_manager.mark_bad(proxy)
                continue
        
        return None

    async def take_screenshot(self, url: str, full_page: bool = False, width: int = 1280, height: int = 720, delay: int = 0, dark_mode: bool = False) -> bytes | None:
        retries = 3
        for attempt in range(retries):
            proxy = await proxy_manager.get_proxy()
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(**self._get_launch_options(proxy))
                    
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
                        
                        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        
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
                        await browser.close()
                        raise e
                        
            except Exception as e:
                logger.warning("screenshot_retry", url=url, attempt=attempt+1, error=str(e), proxy=proxy)
                if proxy:
                    await proxy_manager.mark_bad(proxy)
                continue
        
        return None

headless_service = HeadlessFetcher()
