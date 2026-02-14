from app.services.proxy_manager import proxy_manager

class FetcherService:
    def __init__(self):
        self.ua = UserAgent()
        
        # We don't initialize a single client with a proxy anymore
        # We create clients per request (or session) to switch proxies
        # But for connection pooling efficiency with NO proxy, we keep a default client
        self.default_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            follow_redirects=True,
            verify=False
        )

    async def fetch(self, url: str) -> str:
        # Validate SSRF
        validate_url(url)
        
        headers = { "User-Agent": self.ua.random }
        
        retries = 3
        last_error = None
        
        for attempt in range(retries):
            proxy = await proxy_manager.get_proxy()
            
            # Create a client for this request (needed to set specific proxy)
            # If no proxy, use default_client (but we can't reuse default_client easily if we want different proxies per req)
            # For simplicity in this rotation model, we create a new client or use a helper
            
            try:
                if proxy:
                    async with httpx.AsyncClient(proxies=proxy, verify=False, timeout=10.0, follow_redirects=True) as client:
                        return await self._perform_fetch(client, url, headers)
                else:
                    return await self._perform_fetch(self.default_client, url, headers)
                    
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_error = e
                if proxy:
                    await proxy_manager.mark_bad(proxy)
                logger.warning("fetch_retry", url=url, attempt=attempt+1, error=str(e), proxy=proxy)
                continue
            except Exception as e:
                # Non-retryable or other errors
                raise e
        
        raise last_error or RuntimeError("Fetch failed after retries")

    async def _perform_fetch(self, client, url, headers):
        async with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            content = []
            downloaded = 0
            max_bytes = 2 * 1024 * 1024
            async for chunk in response.aiter_bytes():
                downloaded += len(chunk)
                if downloaded > max_bytes:
                    break
                content.append(chunk)
            return b"".join(content).decode(response.encoding or "utf-8", errors="replace")
            
    async def fetch_json(self, url: str) -> dict | None:
        validate_url(url)
        headers = { "User-Agent": self.ua.random }
        
        retries = 3
        for attempt in range(retries):
            proxy = await proxy_manager.get_proxy()
            try:
                if proxy:
                    async with httpx.AsyncClient(proxies=proxy, verify=False, timeout=10.0) as client:
                        response = await client.get(url, headers=headers)
                        response.raise_for_status()
                        return response.json()
                else:
                    response = await self.default_client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                if proxy:
                    await proxy_manager.mark_bad(proxy)
                logger.warning("fetch_json_retry", url=url, attempt=attempt+1, error=str(e))
                continue
        return None
            
    async def close(self):
        await self.default_client.aclose()

fetcher_service = FetcherService()
