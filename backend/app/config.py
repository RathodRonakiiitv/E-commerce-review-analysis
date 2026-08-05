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
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173,https://review-analyzer-frontend-ochre.vercel.app,https://e-commerce-review-analysis.vercel.app,https://review-analyzer-backend-yy1s.onrender.com"
    cors_origin_regex: str = r"^https://.*\.vercel\.app$"
    
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
    
    # Keep-Alive (Prevent Render Free Tier Sleeping)
    keep_alive_enabled: bool = True
    keep_alive_url: str = ""
    keep_alive_interval_minutes: int = 10

    @property
    def target_keep_alive_url(self) -> str:
        """Resolve target URL for keep-alive ping."""
        url = self.keep_alive_url or os.getenv("RENDER_EXTERNAL_URL", "")
        if url and not url.endswith("/api/health"):
            url = url.rstrip("/") + "/api/health"
        return url
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=('settings_',)
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
