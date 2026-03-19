"""
Configuration management for Cheqroom Webhook Service
Handles environment variables, database setup, and application settings.
"""

import os
from typing import Optional


class Settings:
    """Application settings with environment variable support."""

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_DEBUG: bool = os.getenv("API_DEBUG", "false").lower() == "true"

    # Database Configuration
    DB_USER: str = os.getenv("DB_USER", "propoff")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "student")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "propertyoffice")
    DB_SCHEMA: str = os.getenv("DB_SCHEMA", "public")

    # Build database URL
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Cheqroom Webhook Configuration
    WEBHOOK_SECRET: str = os.getenv(
        "CHEQROOM_WEBHOOK_SECRET",
        "your_webhook_secret_here"  # MUST be overridden in production
    )

    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhooks/cheqroom")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Cheqroom API Configuration (for future use)
    CHEQROOM_API_URL: Optional[str] = os.getenv("CHEQROOM_API_URL")
    CHEQROOM_API_TOKEN: Optional[str] = os.getenv("CHEQROOM_API_TOKEN")

    # Connection Pool Configuration
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))

    @classmethod
    def validate(cls) -> bool:
        """
        Validate critical configuration settings.
        Returns True if valid, raises exception otherwise.
        """
        settings = cls()

        # Check webhook secret
        if settings.WEBHOOK_SECRET == "your_webhook_secret_here":
            raise ValueError(
                "⚠️  CHEQROOM_WEBHOOK_SECRET environment variable not set! "
                "This must be configured in production."
            )

        # Check database connectivity
        if not all([settings.DB_USER, settings.DB_PASSWORD, settings.DB_HOST]):
            raise ValueError(
                "Database credentials not properly configured"
            )

        return True

    def to_dict(self) -> dict:
        """
        Return a dictionary of all settings (sensitive values masked).
        """
        return {
            "api_host": self.API_HOST,
            "api_port": self.API_PORT,
            "api_debug": self.API_DEBUG,
            "database_url": self.DATABASE_URL.replace(
                self.DB_PASSWORD, "***"
            ),
            "webhook_secret": "***" if self.WEBHOOK_SECRET else None,
            "log_level": self.LOG_LEVEL,
            "db_pool_size": self.DB_POOL_SIZE,
            "db_max_overflow": self.DB_MAX_OVERFLOW,
        }


# Global settings instance
settings = Settings()
