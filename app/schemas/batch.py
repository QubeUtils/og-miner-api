from pydantic import BaseModel, Field, HttpUrl
from typing import List
from app.schemas.metadata import ExtractResponse

class BatchExtractRequest(BaseModel):
    urls: List[HttpUrl] = Field(..., min_length=1, max_length=50, description="List of URLs to extract metadata from (max 50).")
    enable_javascript: bool = Field(False, description="Use headless browser for all URLs.")
    force_refresh: bool = Field(False, description="Bypass cache for all URLs.")

class BatchExtractResponse(BaseModel):
    results: dict[str, ExtractResponse | dict] = Field(..., description="Map of URL to extraction result or error.")
    total: int
    successful: int
    failed: int
