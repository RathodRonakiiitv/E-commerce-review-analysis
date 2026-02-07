"""Pydantic schemas for Analysis results."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class SentimentDistribution(BaseModel):
    """Distribution of sentiments."""
    positive: int
    negative: int
    neutral: int
    positive_percent: float
    negative_percent: float
    neutral_percent: float


class SentimentResponse(BaseModel):
    """Overall sentiment analysis response."""
    product_id: int
    overall_score: float = Field(..., ge=0, le=100, description="0-100 sentiment score")
    overall_label: str  # positive, negative, neutral
    distribution: SentimentDistribution
    rating_vs_sentiment_mismatch: int  # Count of mismatched reviews
    total_reviews: int
    analyzed_at: datetime


class AspectSentiment(BaseModel):
    """Sentiment for a single aspect."""
    aspect_name: str
    sentiment_label: str
    average_score: float
    positive_count: int
    negative_count: int
    neutral_count: int
    total_mentions: int
    sample_positive: List[str] = Field(default_factory=list, max_length=3)
    sample_negative: List[str] = Field(default_factory=list, max_length=3)


class AspectResponse(BaseModel):
    """Aspect-based sentiment analysis response."""
    product_id: int
    aspects: List[AspectSentiment]
    analyzed_at: datetime


class TopicKeywords(BaseModel):
    """Topic with its keywords."""
    topic_number: int
    topic_label: str
    keywords: List[str]
    review_count: int
    sample_reviews: List[str] = Field(default_factory=list, max_length=3)


class TopicResponse(BaseModel):
    """Topic modeling response."""
    product_id: int
    topics: List[TopicKeywords]
    analyzed_at: datetime


class InsightsResponse(BaseModel):
    """Key insights summary."""
    product_id: int
    overall_score: float
    total_reviews: int
    avg_rating: float
    
    # Distributions
    rating_distribution: Dict[int, int]  # 1-5 star counts
    sentiment_distribution: SentimentDistribution
    
    # Key findings
    top_positive_reviews: List[Dict[str, Any]]
    top_negative_reviews: List[Dict[str, Any]]
    common_praises: List[str]
    common_complaints: List[str]
    
    # Warnings
    fake_review_count: int
    fake_review_percent: float
    
    analyzed_at: datetime


class ComparisonRequest(BaseModel):
    """Request to compare products."""
    product_ids: List[int] = Field(..., min_length=2, max_length=3)


class ProductComparison(BaseModel):
    """Comparison data for a single product."""
    product_id: int
    product_name: Optional[str]
    overall_score: float
    avg_rating: float
    total_reviews: int
    aspects: Dict[str, float]  # aspect_name -> score


class ComparisonResponse(BaseModel):
    """Product comparison response."""
    products: List[ProductComparison]
    best_overall: int  # product_id
    aspect_winners: Dict[str, int]  # aspect_name -> product_id
    created_at: datetime
