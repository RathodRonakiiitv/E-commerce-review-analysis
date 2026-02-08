"""Application configuration using Pydantic Settings."""
import os
from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env path relative to backend/ directory (parent of app/)
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = str(BACKEND_DIR / ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./reviews.db"
    
    # API
    api_secret_key: str = "dev-secret-key"
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173"
    
    # Scraping
    request_timeout: int = 10
    max_retries: int = 3
    scrape_delay_min: float = 2.0
    scrape_delay_max: float = 4.0
    
    # ML
    model_cache_dir: str = "./models_cache"
    sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    
    # Groq AI
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
