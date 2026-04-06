"""
Configuration settings for PDF to Word Converter API
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # API
    api_key: str = "dev-api-key-change-in-production"

    # File handling
    max_file_size: int = 20 * 1024 * 1024  # 20MB in bytes
    file_retention_minutes: int = 30
    uploads_dir: str = "uploads"
    outputs_dir: str = "outputs"
    logs_dir: str = "logs"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Logging
    log_level: str = "INFO"

    # Rate limiting
    rate_limit: str = "10/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
