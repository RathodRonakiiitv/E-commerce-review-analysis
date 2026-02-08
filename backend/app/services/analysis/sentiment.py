"""Sentiment analysis service using HuggingFace Transformers."""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Product, Review
from app.config import get_settings

settings = get_settings()

# Lazy-loaded transformer pipeline
_sentiment_pipeline = None


def get_sentiment_pipeline():
    """Get or create the sentiment analysis pipeline."""
    global _sentiment_pipeline
    
    if _sentiment_pipeline is None:
        from transformers import pipeline
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=settings.sentiment_model,
            device=-1  # CPU, use 0 for GPU
        )
        print(f"[OK] Loaded sentiment model: {settings.sentiment_model}")
    
    return _sentiment_pipeline


def analyze_text(text: str) -> Tuple[str, float]:
    """
    Analyze sentiment of a single text.
    
    Returns:
        Tuple of (label, score) where label is 'positive', 'negative', or 'neutral'
    """
    if not text or len(text.strip()) < 3:
        return "neutral", 0.5
    
    # Truncate long texts (transformer limit)
    text = text[:512]
    
    try:
        pipeline = get_sentiment_pipeline()
        result = pipeline(text)[0]
        
        label = result['label'].lower()
        score = result['score']
        
        # Map LABEL_0/LABEL_1 or POSITIVE/NEGATIVE
        if 'positive' in label or label == 'label_1':
            return 'positive', score
        elif 'negative' in label or label == 'label_0':
            return 'negative', score
        else:
            return 'neutral', score
    
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return "neutral", 0.5


def analyze_texts_batch(texts: List[str], batch_size: int = 32) -> List[Tuple[str, float]]:
    """
    Analyze sentiment of multiple texts in batches.
    
    Returns:
        List of (label, score) tuples
    """
    results = []
    pipeline = get_sentiment_pipeline()
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        # Truncate and clean
        batch = [t[:512] if t else "" for t in batch]
        
        try:
            batch_results = pipeline(batch)
            
            for result in batch_results:
                label = result['label'].lower()
                score = result['score']
                
                if 'positive' in label or label == 'label_1':
                    results.append(('positive', score))
                elif 'negative' in label or label == 'label_0':
                    results.append(('negative', score))
                else:
                    results.append(('neutral', score))
        
        except Exception as e:
            print(f"Batch analysis error: {e}")
            # Fill with neutral for failed batch
            results.extend([('neutral', 0.5)] * len(batch))
    
    return results


async def analyze_product_sentiment(db: Session, product_id: int) -> Dict:
    """
    Analyze overall sentiment for a product.
    
    Returns:
        Dictionary with sentiment analysis results
    """
    # Get all reviews
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    if not reviews:
        return {
            "product_id": product_id,
            "overall_score": 50.0,
            "overall_label": "neutral",
            "distribution": {
                "positive": 0, "negative": 0, "neutral": 0,
                "positive_percent": 0, "negative_percent": 0, "neutral_percent": 0
            },
            "rating_vs_sentiment_mismatch": 0,
            "total_reviews": 0,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    # Get texts for batch analysis
    texts = [r.review_text for r in reviews]
    
    # Analyze all texts
    sentiments = await asyncio.to_thread(analyze_texts_batch, texts)
    
    # Update reviews with sentiment
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    mismatch_count = 0
    total_score = 0
    
    for review, (label, score) in zip(reviews, sentiments):
        review.sentiment_label = label
        review.sentiment_score = score
        review.analyzed_at = datetime.utcnow()
        
        if label == 'positive':
            positive_count += 1
            total_score += score
        elif label == 'negative':
            negative_count += 1
            total_score -= score
        else:
            neutral_count += 1
        
        # Check for rating/sentiment mismatch
        if (label == 'positive' and review.rating <= 2) or \
           (label == 'negative' and review.rating >= 4):
            mismatch_count += 1
    
    db.commit()
    
    # Calculate percentages
    total = len(reviews)
    
    # Overall score: normalize to 0-100
    # Positive adds, negative subtracts
    normalized_score = ((total_score / total) + 1) / 2 * 100  # Convert -1..1 to 0..100
    overall_score = max(0, min(100, normalized_score))
    
    # Determine overall label based on score
    if overall_score >= 60:
        overall_label = "positive"
    elif overall_score <= 40:
        overall_label = "negative"
    else:
        overall_label = "neutral"
    
    # Update product
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.last_analyzed = datetime.utcnow()
        db.commit()
    
    return {
        "product_id": product_id,
        "overall_score": round(overall_score, 2),
        "overall_label": overall_label,
        "distribution": {
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count,
            "positive_percent": round(positive_count / total * 100, 1),
            "negative_percent": round(negative_count / total * 100, 1),
            "neutral_percent": round(neutral_count / total * 100, 1)
        },
        "rating_vs_sentiment_mismatch": mismatch_count,
        "total_reviews": total,
        "analyzed_at": datetime.utcnow().isoformat()
    }
