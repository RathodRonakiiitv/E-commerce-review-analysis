"""Pydantic schemas for Product operations."""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, HttpUrl, Field


class ProductBase(BaseModel):
    """Base product fields."""
    name: Optional[str] = None
    url: str
    platform: str = "amazon"


class ProductCreate(BaseModel):
    """Schema for creating a product via scraping."""
    url: str = Field(..., description="Product URL from Amazon or Flipkart")
    max_reviews: int = Field(default=200, ge=10, le=500, description="Max reviews to scrape")


class ProductUpdate(BaseModel):
    """Schema for updating product information."""
    name: Optional[str] = None


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: int
    name: Optional[str]
    url: str
    platform: str
    total_reviews: int
    avg_rating: Optional[Decimal]
    scraped_at: Optional[datetime]
    last_analyzed: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list."""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
