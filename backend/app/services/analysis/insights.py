"""Insights generator - aggregates all analysis into key findings."""
from datetime import datetime
from typing import Dict
from collections import Counter

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Product, Review


async def generate_product_insights(db: Session, product_id: int) -> Dict:
    """
    Generate comprehensive insights summary for a product.
    
    Returns:
        Dictionary with key insights and findings
    """
    # Get product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product {product_id} not found")
    
    # Get all reviews
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    if not reviews:
        return {
            "product_id": product_id,
            "overall_score": 50.0,
            "total_reviews": 0,
            "avg_rating": 0.0,
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "sentiment_distribution": {
                "positive": 0, "negative": 0, "neutral": 0,
                "positive_percent": 0, "negative_percent": 0, "neutral_percent": 0
            },
            "top_positive_reviews": [],
            "top_negative_reviews": [],
            "common_praises": [],
            "common_complaints": [],
            "fake_review_count": 0,
            "fake_review_percent": 0.0,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    # Calculate rating distribution
    rating_dist = Counter(r.rating for r in reviews)
    rating_distribution = {i: rating_dist.get(i, 0) for i in range(1, 6)}
    
    # Calculate sentiment distribution
    sentiment_dist = Counter(r.sentiment_label for r in reviews if r.sentiment_label)
    total_analyzed = sum(sentiment_dist.values())
    
    sentiment_distribution = {
        "positive": sentiment_dist.get("positive", 0),
        "negative": sentiment_dist.get("negative", 0),
        "neutral": sentiment_dist.get("neutral", 0),
        "positive_percent": round(sentiment_dist.get("positive", 0) / max(total_analyzed, 1) * 100, 1),
        "negative_percent": round(sentiment_dist.get("negative", 0) / max(total_analyzed, 1) * 100, 1),
        "neutral_percent": round(sentiment_dist.get("neutral", 0) / max(total_analyzed, 1) * 100, 1)
    }
    
    # Calculate overall score (weighted average of sentiment and ratings)
    avg_rating = sum(r.rating for r in reviews) / len(reviews)
    rating_score = (avg_rating / 5) * 100
    
    sentiment_score = 50.0
    if total_analyzed > 0:
        positive_ratio = sentiment_dist.get("positive", 0) / total_analyzed
        negative_ratio = sentiment_dist.get("negative", 0) / total_analyzed
        sentiment_score = (positive_ratio - negative_ratio + 1) / 2 * 100
    
    # Weighted: 60% sentiment, 40% rating
    overall_score = sentiment_score * 0.6 + rating_score * 0.4
    
    # Get top positive reviews
    positive_reviews = [r for r in reviews if r.sentiment_label == "positive"]
    positive_reviews.sort(key=lambda r: (r.sentiment_score or 0, r.rating), reverse=True)
    top_positive = [
        {
            "id": r.id,
            "text": r.review_text[:300] + "..." if len(r.review_text) > 300 else r.review_text,
            "rating": r.rating,
            "sentiment_score": float(r.sentiment_score) if r.sentiment_score else None
        }
        for r in positive_reviews[:5]
    ]
    
    # Get top negative reviews
    negative_reviews = [r for r in reviews if r.sentiment_label == "negative"]
    negative_reviews.sort(key=lambda r: (r.sentiment_score or 0, -r.rating), reverse=True)
    top_negative = [
        {
            "id": r.id,
            "text": r.review_text[:300] + "..." if len(r.review_text) > 300 else r.review_text,
            "rating": r.rating,
            "sentiment_score": float(r.sentiment_score) if r.sentiment_score else None
        }
        for r in negative_reviews[:5]
    ]
    
    # Extract common words from positive/negative reviews
    common_praises = extract_common_keywords(positive_reviews, positive=True)
    common_complaints = extract_common_keywords(negative_reviews, positive=False)
    
    # Count fake reviews
    fake_count = sum(1 for r in reviews if r.is_suspicious)
    fake_percent = round(fake_count / len(reviews) * 100, 1)
    
    return {
        "product_id": product_id,
        "overall_score": round(overall_score, 2),
        "total_reviews": len(reviews),
        "avg_rating": round(avg_rating, 2),
        "rating_distribution": rating_distribution,
        "sentiment_distribution": sentiment_distribution,
        "top_positive_reviews": top_positive,
        "top_negative_reviews": top_negative,
        "common_praises": common_praises,
        "common_complaints": common_complaints,
        "fake_review_count": fake_count,
        "fake_review_percent": fake_percent,
        "analyzed_at": datetime.utcnow().isoformat()
    }


def extract_common_keywords(reviews, positive: bool = True, top_n: int = 10):
    """Extract common meaningful keywords from reviews."""
    # Stopwords and common words to exclude
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "again", "further", "then", "once", "here",
        "there", "when", "where", "why", "how", "all", "each", "every", "both",
        "few", "more", "most", "other", "some", "such", "no", "nor", "not",
        "only", "own", "same", "so", "than", "too", "very", "just", "also",
        "and", "but", "or", "if", "because", "while", "although", "this",
        "that", "these", "those", "i", "me", "my", "we", "our", "you", "your",
        "he", "she", "it", "they", "them", "its", "product", "amazon", "flipkart",
        "buy", "bought", "one", "get", "got", "use", "using", "like", "really",
        "much", "even", "still", "well", "back", "time", "thing", "things"
    }
    
    # Positive/negative specific keywords to highlight
    positive_terms = {
        "excellent", "amazing", "awesome", "fantastic", "wonderful", "perfect",
        "great", "love", "best", "superb", "brilliant", "outstanding", "incredible",
        "smooth", "fast", "beautiful", "comfortable", "reliable", "durable"
    }
    
    negative_terms = {
        "terrible", "horrible", "awful", "poor", "bad", "worst", "disappointing",
        "broken", "defective", "cheap", "slow", "waste", "useless", "damaged",
        "fake", "faulty", "unreliable", "uncomfortable", "fragile"
    }
    
    word_counts = Counter()
    target_terms = positive_terms if positive else negative_terms
    
    for review in reviews:
        words = review.review_text.lower().split()
        # Clean words
        words = [w.strip('.,!?";:()[]{}') for w in words]
        words = [w for w in words if len(w) > 2 and w not in stopwords]
        
        # Boost target terms
        for word in words:
            if word in target_terms:
                word_counts[word] += 3
            else:
                word_counts[word] += 1
    
    # Get top keywords
    return [word for word, _ in word_counts.most_common(top_n)]
