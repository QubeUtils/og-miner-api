from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices


class Settings(BaseSettings):
    PROJECT_NAME: str = "OG Miner: OpenGraph Miner"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str = "High Performance OpenGraph Miner backed by FastAPI and Redis. Supports Headless Browser execution for SPAs, SSRF protection, and rich data extraction including OpenGraph, Twitter Cards, and JSON-LD."
    CONTACT: dict = {
        "name": "Kavindu Gunasena",
        "url": "https://www.linkedin.com/in/sasmithakg/"
    }
    
    # Redis
    REDIS_URL: str = Field("redis://localhost:6379/0", validation_alias=AliasChoices("REDIS_URL", "REDISCLOUD_URL"))
    
    # Security
    SECRET_KEY: str = "change_this_to_a_secure_random_string"
    X_RAPIDAPI_PROXY_SECRET: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )


settings = Settings()
