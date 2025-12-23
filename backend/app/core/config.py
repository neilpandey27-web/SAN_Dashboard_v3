"""
Application configuration using Pydantic Settings.
Loads from environment variables or .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "OneIT SAN Analytics"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    
    # Database
    # For Docker: Uses PostgreSQL container from docker-compose.yml
    # For local development without Docker: Can use SQLite
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/storage_insights"
    # For SQLite (local only): "sqlite:///../db_files/storage_insights.db"
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS",
        description="Allowed CORS origins (comma-separated)"
    )
    
    # SMTP Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@company.com"
    SMTP_FROM_NAME: str = "OneIT SAN Analytics"
    SMTP_TLS: bool = True
    
    # Frontend URL for email links
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".xlsx", ".xls"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
