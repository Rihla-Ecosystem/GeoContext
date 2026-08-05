from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "GeoContext"
    
    # Environment
    ENVIRONMENT: str = Field(
        default="local", 
        description="Environment name (local, staging, production)",
    )

    # Database connection
    DATABASE_URL: str = Field(
        description="Database connection string (asyncpg)",
    )

    # JWT Authentication (HS256 — shared secret with Core-Server)
    JWT_ACCESS_SECRET: str = Field(
        description="Shared JWT secret for verifying tokens issued by Core-Server"
    )
    INTERNAL_API_KEY: str = Field(
        default="",
        description="Internal API key for Core-Server gateway calls (X-Internal-Api-Key header)"
    )
    CORE_SERVER_URL: str = Field(
        default="http://localhost:3000",
        description="Base URL of the Core-Server (used for admin credential verification)"
    )
    ADMIN_BOOTSTRAP_SECRET: str = Field(
        default="change-me-in-production",
        description="Temporary bypass secret for admin panel access"
    )

    # SQLAdmin dashboard credentials
    ADMIN_USERNAME: str = Field(
        default="admin",
        description="Username for the SQLAdmin dashboard login"
    )
    ADMIN_PASSWORD: str = Field(
        default="Admin123!",
        description="Password for the SQLAdmin dashboard login"
    )

    # CORS origins
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="List of allowed CORS origins",
    )

    # Rate limits
    RATE_LIMIT_GLOBAL: str = Field(
        default="100/minute",
        description="Global rate limit string for slowapi",
    )

    # Business Logic Defaults
    DEFAULT_DETECTION_RADIUS: float = Field(
        default=1000.0,
        description="Default detection radius in meters for nearby sites",
    )
    MAX_DETECTION_RADIUS: float = Field(
        default=5000.0,
        description="Maximum allowed detection radius in meters",
    )
    AT_SITE_RADIUS: float = Field(
        default=50.0,
        description="Radius in meters to consider a user 'at' a site",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()