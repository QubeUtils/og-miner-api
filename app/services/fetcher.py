import httpx
from fake_useragent import UserAgent
from app.core.security import validate_url
from app.utils.logger import logger

class FetcherService:
    def __init__(self):
        self.ua = UserAgent()
        
        # Configure Proxies
        proxies = None
        if hasattr(settings, "PROXY_URL") and settings.PROXY_URL:
            proxies = settings.PROXY_URL
            logger.info("fetcher_proxy_enabled")

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            follow_redirects=True,
            verify=False,
            proxies=proxies
        )

    async def fetch(self, url: str) -> str:
        # Validate SSRF
        validate_url(url)
        
        headers = {
            "User-Agent": self.ua.random
        }

        try:
            async with self.client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()
                
                content = []
                downloaded = 0
                max_bytes = 2 * 1024 * 1024  # 2MB limit
                
                async for chunk in response.aiter_bytes():
                    downloaded += len(chunk)
                    if downloaded > max_bytes:
                        logger.warning("fetch_size_limit_exceeded", url=url, size=downloaded)
                        break 
                    content.append(chunk)

                raw_content = b"".join(content)
                
                # Charset Detection
                encoding = response.encoding or "utf-8"
                
                # Heuristic fallback if httpx returns None or ISO-8859-1 (often default when unknown) 
                # Ideally we used `chardet` but let's trust httpx + errors='replace' for now as per plan
                return raw_content.decode(encoding, errors="replace")
                
        except httpx.TimeoutException as e:
            logger.error("fetch_timeout", url=url, error=str(e))
            raise TimeoutError(f"Request timed out: {str(e)}")
        except httpx.ConnectError as e:
            logger.error("fetch_connection_error", url=url, error=str(e))
            raise ConnectionError(f"Connection failed: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error("fetch_http_error", url=url, status_code=e.response.status_code)
            raise ValueError(f"HTTP Error {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("fetch_request_error", url=url, error=str(e))
            raise RuntimeError(f"Request failed: {str(e)}")
            
    async def fetch_json(self, url: str) -> dict | None:
        validate_url(url)
        headers = { "User-Agent": self.ua.random }
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("fetch_json_failed", url=url, error=str(e))
            return None
            
    async def close(self):
        await self.client.aclose()

fetcher_service = FetcherService()
