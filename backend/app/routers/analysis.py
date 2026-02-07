"""Analysis endpoints for sentiment, aspects, topics, and insights."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Review, AnalysisCache
from app.schemas.analysis import (
    SentimentResponse, AspectResponse, TopicResponse, InsightsResponse
)

router = APIRouter()


def get_cached_analysis(db: Session, product_id: int, analysis_type: str):
    """Get cached analysis if exists and not expired."""
    cache = (
        db.query(AnalysisCache)
        .filter(
            AnalysisCache.product_id == product_id,
            AnalysisCache.analysis_type == analysis_type
        )
        .order_by(AnalysisCache.created_at.desc())
        .first()
    )
    
    if cache:
        # Check if cache is less than 24 hours old
        age = (datetime.utcnow() - cache.created_at).total_seconds()
        if age < 86400:  # 24 hours
            return cache.results
    
    return None


def save_analysis_cache(db: Session, product_id: int, analysis_type: str, results: dict):
    """Save analysis results to cache."""
    cache = AnalysisCache(
        product_id=product_id,
        analysis_type=analysis_type,
        results=results
    )
    db.add(cache)
    db.commit()


@router.get("/{product_id}/sentiment", response_model=SentimentResponse)
async def get_sentiment_analysis(
    product_id: int,
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """Get overall sentiment analysis for a product."""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check cache
    if not force_refresh:
        cached = get_cached_analysis(db, product_id, "sentiment")
        if cached:
            return SentimentResponse(**cached)
    
    # Run analysis
    from app.services.analysis.sentiment import analyze_product_sentiment
    results = await analyze_product_sentiment(db, product_id)
    
    # Cache results
    save_analysis_cache(db, product_id, "sentiment", results)
    
    return SentimentResponse(**results)


@router.get("/{product_id}/aspects", response_model=AspectResponse)
async def get_aspect_analysis(
    product_id: int,
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """Get aspect-based sentiment analysis."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not force_refresh:
        cached = get_cached_analysis(db, product_id, "aspects")
        if cached:
            return AspectResponse(**cached)
    
    from app.services.analysis.aspects import analyze_product_aspects
    results = await analyze_product_aspects(db, product_id)
    
    save_analysis_cache(db, product_id, "aspects", results)
    
    return AspectResponse(**results)


@router.get("/{product_id}/topics", response_model=TopicResponse)
async def get_topic_analysis(
    product_id: int,
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """Get topic modeling results."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not force_refresh:
        cached = get_cached_analysis(db, product_id, "topics")
        if cached:
            return TopicResponse(**cached)
    
    from app.services.analysis.topics import analyze_product_topics
    results = await analyze_product_topics(db, product_id)
    
    save_analysis_cache(db, product_id, "topics", results)
    
    return TopicResponse(**results)


@router.get("/{product_id}/insights", response_model=InsightsResponse)
async def get_insights(
    product_id: int,
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """Get key insights and summary for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not force_refresh:
        cached = get_cached_analysis(db, product_id, "insights")
        if cached:
            return InsightsResponse(**cached)
    
    from app.services.analysis.insights import generate_product_insights
    results = await generate_product_insights(db, product_id)
    
    save_analysis_cache(db, product_id, "insights", results)
    
    return InsightsResponse(**results)


@router.post("/{product_id}/reanalyze")
async def reanalyze_product(
    product_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger a fresh analysis of all reviews."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Clear existing cache
    db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).delete()
    db.commit()
    
    # Queue background re-analysis
    async def run_full_analysis():
        from app.services.analysis import run_complete_analysis
        await run_complete_analysis(product_id)
    
    background_tasks.add_task(run_full_analysis)
    
    return {"message": "Re-analysis started", "product_id": product_id}
