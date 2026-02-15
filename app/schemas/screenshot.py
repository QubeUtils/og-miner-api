from pydantic import BaseModel, HttpUrl, Field

class ScreenshotRequest(BaseModel):
    url: HttpUrl
    full_page: bool = False
    width: int = Field(1280, ge=320, le=3840)
    height: int = Field(720, ge=240, le=2160)
    delay: int = Field(0, ge=0, le=10000, description="Delay in milliseconds")
    dark_mode: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://stripe.com",
                # "viewport": {"width": 1280, "height": 720}, # Not in schema, but typical for screenshot
                "full_page": True,
                "dark_mode": True
            }
        }
    }
