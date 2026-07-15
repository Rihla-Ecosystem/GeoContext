from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "GeoContext"

    # Database connection
    DATABASE_URL: str = Field(
        description="Database connection string (asyncpg)",
    )

    # JWT Authentication
    JWT_PUBLIC_KEY: str = Field(
        description="Public key for verifying JWT tokens"
    )
    JWT_ALGORITHM: str = "RS256"

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
        default=50.0,
        description="Default detection radius in meters for geofencing",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()