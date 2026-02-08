"""AI-powered insights router using Groq API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models import Product, Review
from app.services.ai.groq_service import groq_service


router = APIRouter(prefix="/ai")


class AIInsightsResponse(BaseModel):
    summary: Optional[str]
    model: Optional[str]
    reviews_analyzed: Optional[int]
    error: Optional[str]


class AspectDeepDiveRequest(BaseModel):
    aspect: str


class ReviewResponseRequest(BaseModel):
    review_text: str
    sentiment: str = "neutral"


@router.get("/products/{product_id}/ai-summary", response_model=AIInsightsResponse)
async def get_ai_summary(product_id: int, db: Session = Depends(get_db)):
    """
    Get AI-generated summary of product reviews using Groq API.
    
    Returns executive summary, strengths, weaknesses, and recommendations.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this product")
    
    # Prepare review data
    review_data = [
        {
            "text": r.review_text,
            "rating": r.rating,
            "sentiment": r.sentiment_label or "unknown"
        }
        for r in reviews
    ]
    
    result = await groq_service.generate_review_summary(review_data, product.name or "Product")
    return result


@router.post("/products/{product_id}/aspect-dive")
async def get_aspect_deep_dive(
    product_id: int, 
    request: AspectDeepDiveRequest,
    db: Session = Depends(get_db)
):
    """
    Get AI-generated deep dive analysis for a specific aspect.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    review_data = [{"text": r.review_text, "rating": r.rating} for r in reviews]
    
    result = await groq_service.generate_aspect_deep_dive(
        request.aspect, 
        review_data, 
        product.name or "Product"
    )
    return result


@router.post("/suggest-response")
async def suggest_review_response(request: ReviewResponseRequest):
    """
    Generate a suggested seller response to a customer review.
    """
    result = await groq_service.suggest_response_to_review(
        request.review_text,
        request.sentiment
    )
    return result


@router.get("/health")
async def ai_health_check():
    """Check if Groq API is configured."""
    from app.config import get_settings
    settings = get_settings()
    return {
        "groq_configured": bool(settings.groq_api_key),
        "model": settings.groq_model,
        "api_key_prefix": settings.groq_api_key[:8] + "..." if settings.groq_api_key else "not set"
    }
