import time
from urllib.parse import urlparse
from app.schemas.metadata import ExtractRequest, ExtractResponse, Metadata, MetaInfo
from app.utils.logger import logger

class ExtractService:
    def __init__(self, cache_service, fetcher_service, parser_service, headless_service):
        self.cache = cache_service
        self.fetcher = fetcher_service
        self.parser = parser_service
        self.headless = headless_service

    async def extract_metadata(self, request: ExtractRequest) -> dict:
        start_time = time.time()
        url_str = str(request.url)
        domain = urlparse(url_str).netloc
        
        # Check cache
        if not request.force_refresh:
            cached_data = await self.cache.get(f"metadata:{url_str}")
            if cached_data:
                latency = (time.time() - start_time) * 1000
                logger.info("cache_hit", url=url_str, latency=latency)
                # Return dict properly formatted for response construction in API
                return {
                    "meta": MetaInfo(url=url_str, domain=domain, latency_ms=latency),
                    "data": Metadata(**cached_data)
                }

        # Fetch and Parse
        try:
            html_content = None
            
            # 1. Try Headless if requested
            if request.enable_javascript:
                # Convert cookies dict to list of dicts for Playwright if needed
                pw_cookies = []
                if request.cookies:
                    for k, v in request.cookies.items():
                        pw_cookies.append({"name": k, "value": v, "url": url_str})

                # Note: This might be slow. Client should be aware (timeout increased?)
                html_content = await self.headless.fetch_and_render(url_str, cookies=pw_cookies, country=request.country)
                if html_content:
                    logger.info("headless_fetch_success", url=url_str)
                else:
                    logger.warning("headless_fetch_empty_fallback", url=url_str)
            
            # 2. Standard Fetch (Fallback or Default)
            if not html_content:
                html_content = await self.fetcher.fetch(url_str, cookies=request.cookies, country=request.country)

            metadata_dict = self.parser.parse(html_content, url_str)
            
            # oEmbed Fetching (Standard fetch, no cookies/country needed typically, but could pass if we wanted)
            oembed_url = metadata_dict.pop("oembed_url", None)
            if oembed_url:
                # We treat oEmbed failure as non-critical
                # We use default fetch_json which uses proxy rotation but maybe not cookies. 
                # Keeping it simple for now.
                oembed_data = await self.fetcher.fetch_json(oembed_url)
                if oembed_data:
                    metadata_dict["oembed"] = oembed_data
            
            # Cache Result
            await self.cache.set(f"metadata:{url_str}", metadata_dict, ttl=86400)
            
            latency = (time.time() - start_time) * 1000
            logger.info("extraction_success", url=url_str, latency=latency, method="headless" if request.enable_javascript and html_content else "standard")
            
            return {
                "meta": MetaInfo(url=url_str, domain=domain, latency_ms=latency),
                "data": Metadata(**metadata_dict)
            }
            
        except Exception as e:
            # Re-raise to be handled by API layer or return error dict
            raise e
