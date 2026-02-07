"""Pydantic schemas for Scraping operations."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of a scraping job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapeRequest(BaseModel):
    """Request to start scraping a product."""
    url: str = Field(..., description="Product URL from Amazon or Flipkart")
    max_reviews: int = Field(default=200, ge=10, le=500, description="Max reviews to scrape")


class ScrapeStatusResponse(BaseModel):
    """Status of a scraping job."""
    job_id: str
    status: JobStatus
    product_id: Optional[int] = None
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    reviews_scraped: int = 0
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
