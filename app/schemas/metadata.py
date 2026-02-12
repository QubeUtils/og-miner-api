from pydantic import BaseModel, HttpUrl, Field

class ExtractRequest(BaseModel):
    url: HttpUrl
    force_refresh: bool = False
    enable_javascript: bool = False

class Metadata(BaseModel):
    title: str | None = None
    description: str | None = None
    favicon: str | None = None
    image: str | None = None
    author: str | None = None
    site_name: str | None = None
    canonical_url: str | None = None
    oembed: dict | None = None
    json_ld: list | dict | None = None

class MetaInfo(BaseModel):
    url: str
    domain: str
    latency_ms: float

class ExtractResponse(BaseModel):
    meta: MetaInfo
    data: Metadata
