import httpx
import asyncio
import random
from typing import Optional
from app.utils.logger import logger
from app.core.config import settings

class ProxyManager:
    def __init__(self):
        self.proxies: list[str] = []
        self.bad_proxies: set[str] = set()
        self.static_proxy = settings.PROXY_URL
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Fetch initial list of proxies if no static proxy is configured."""
        if self.static_proxy:
            logger.info("using_static_proxy", proxy=self.static_proxy)
            return

        await self.refresh_proxies()

    async def refresh_proxies(self):
        """Fetches free proxies from public sources."""
        logger.info("refreshing_free_proxies")
        found_proxies = []
        
        # Source 1: Proxyscrape (HTTP/S)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
                )
                if response.status_code == 200:
                    lines = response.text.splitlines()
                    # Basic validation of format host:port
                    found_proxies.extend([f"http://{line.strip()}" for line in lines if line.strip() and ":" in line])
        except Exception as e:
            logger.error("proxy_refresh_failed", source="proxyscrape", error=str(e))

        # Deduplicate and update
        if found_proxies:
            async with self._lock:
                self.proxies = list(set(found_proxies))
                self.bad_proxies.clear() # Reset bad proxies on refresh
            logger.info("proxy_refresh_success", count=len(self.proxies))
        else:
            logger.warning("proxy_refresh_no_proxies_found")

    async def get_proxy(self) -> Optional[str]:
        """Returns a proxy to use. Prioritizes static proxy."""
        if self.static_proxy:
            return self.static_proxy

        async with self._lock:
            if not self.proxies:
                return None
            
            # Simple random selection for now, avoiding known bad ones if possible
            # If all are bad, we might need to recycle or refresh
            available = [p for p in self.proxies if p not in self.bad_proxies]
            
            if not available:
                if not self.proxies:
                     # Emergency refresh if empty
                    taskId = asyncio.create_task(self.refresh_proxies())
                    return None
                # If all marked bad, reset bad list and try again (maybe they recovered)
                self.bad_proxies.clear()
                available = self.proxies

            return random.choice(available)

    async def mark_bad(self, proxy: str):
        """Marks a proxy as bad so it's avoided for a while."""
        if proxy == self.static_proxy:
            return # Don't mark static proxy as bad, just log error elsewhere

        async with self._lock:
            self.bad_proxies.add(proxy)
            
            # If too many bad proxies, trigger refresh
            if len(self.proxies) > 0 and len(self.bad_proxies) / len(self.proxies) > 0.8:
                 # Trigger background refresh if 80% are bad
                 asyncio.create_task(self.refresh_proxies())

proxy_manager = ProxyManager()
