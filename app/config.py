"""
Application configuration from environment variables.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


def _detect_postgres_host() -> str:
    """Detect PostgreSQL host based on environment."""
    # Check if we're in Docker (container name or hostname)
    if os.path.exists("/.dockerenv") or os.environ.get("POSTGRES_HOST"):
        return os.environ.get("POSTGRES_HOST", "postgres")
    # Default to localhost for local development
    return "localhost"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database configuration
    POSTGRES_DB: str = "enrichment_db"
    POSTGRES_USER: str = "enrichment_user"
    POSTGRES_PASSWORD: str = "enrichment_pass"
    POSTGRES_HOST: str = _detect_postgres_host()
    POSTGRES_PORT: int = 5432
    
    # Computed DATABASE_URL
    @property
    def DATABASE_URL(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # Application settings
    LOG_LEVEL: str = "INFO"
    ENRICHMENT_DB_PATH: Optional[str] = None  # Legacy SQLite path (optional)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
