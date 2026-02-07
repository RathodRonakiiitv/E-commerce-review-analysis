"""Pydantic schemas for Review operations."""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    """Base review fields."""
    review_text: str
    rating: int = Field(..., ge=1, le=5)
    review_date: Optional[date] = None
    reviewer_name: Optional[str] = None
    verified_purchase: bool = False
    helpful_count: int = 0


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""
    product_id: int


class ReviewResponse(BaseModel):
    """Schema for review response."""
    id: int
    product_id: int
    review_text: str
    rating: int
    review_date: Optional[date]
    reviewer_name: Optional[str]
    verified_purchase: bool
    helpful_count: int
    sentiment_label: Optional[str]
    sentiment_score: Optional[Decimal]
    is_suspicious: bool
    suspicious_score: int
    scraped_at: datetime
    analyzed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Schema for paginated review list."""
    items: List[ReviewResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReviewWithAspects(ReviewResponse):
    """Review response including aspect details."""
    aspects: List["AspectDetail"] = []


class AspectDetail(BaseModel):
    """Detail of an aspect mentioned in a review."""
    aspect_name: str
    sentiment: Optional[str]
    sentiment_score: Optional[Decimal]
    mentioned_text: Optional[str]
    
    class Config:
        from_attributes = True
