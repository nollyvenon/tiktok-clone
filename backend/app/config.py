"""
Application configuration and settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # App
    APP_NAME: str = "TikTok Clone API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "postgresql://tiktok_user:tiktok_password@localhost:5432/tiktok_clone"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    # JWT & Security
    JWT_SECRET_KEY: str = "your_super_secret_key_change_in_production_NOW"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    # Hashing
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 128

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "tiktok-clone-videos"
    S3_BUCKET_URL: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@tiktok-clone.com"
    SENDGRID_API_KEY: Optional[str] = None

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # OAuth Providers (to be configured)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_TEAM_ID: Optional[str] = None
    FACEBOOK_CLIENT_ID: Optional[str] = None
    FACEBOOK_CLIENT_SECRET: Optional[str] = None
    TIKTOK_CLIENT_ID: Optional[str] = None
    TIKTOK_CLIENT_SECRET: Optional[str] = None
    OAUTH_STATE_SECRET: str = "oauth_state_secret_change_in_production"
    OAUTH_STATE_TTL_SECONDS: int = 600

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
