import httpx
import io
from PIL import Image
from app.services.proxy_manager import proxy_manager
from app.utils.logger import logger

from pydantic import BaseModel

class ResizeParams(BaseModel):
    width: int | None = None
    height: int | None = None

class ImageProxyService:
    async def fetch_image(self, url: str) -> bytes | None:
        """
        Fetches an image from a URL using rotating proxies.
        """
        retries = 3
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"
        }

        for attempt in range(retries):
            proxy = await proxy_manager.get_proxy()
            try:
                # We need a new client per request to switch proxies easily in this simple architecture
                async with httpx.AsyncClient(proxies=proxy, verify=False, timeout=10.0, follow_redirects=True) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    
                    # Verify it's an image
                    content_type = response.headers.get("content-type", "")
                    if "image" not in content_type:
                        logger.warning("image_proxy_invalid_content_type", url=url, type=content_type)
                        return None
                        
                    return response.content
                    
            except Exception as e:
                logger.warning("image_proxy_retry", url=url, attempt=attempt+1, error=str(e), proxy=proxy)
                if proxy:
                    await proxy_manager.mark_bad(proxy)
                continue
        
        return None

    def process_image(self, image_bytes: bytes, width: int | None = None, height: int | None = None) -> tuple[bytes, str]:
        """
        Resizes and converts image to WebP (default).
        Returns (image_bytes, media_type).
        """
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Convert to RGB if necessary (e.g. for PNGs with transparency if saving as JPEG, but we use WebP which supports safe RGBA)
                if img.mode in ("RGBA", "LA") and False: # Keep transparency for WebP
                    background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
                    background.paste(img, img.split()[-1])
                    img = background

                # Resize if requested
                if width or height:
                    # Calculate new dimensions preserving aspect ratio if only one dim provided
                    current_w, current_h = img.size
                    
                    if width and height:
                        new_size = (width, height)
                    elif width:
                        ratio = width / current_w
                        new_size = (width, int(current_h * ratio))
                    elif height:
                        ratio = height / current_h
                        new_size = (int(current_w * ratio), height)
                    
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                output = io.BytesIO()
                img.save(output, format="WEBP", quality=85)
                return output.getvalue(), "image/webp"
                
        except Exception as e:
            logger.error("image_processing_failed", error=str(e))
            raise e

image_proxy_service = ImageProxyService()
