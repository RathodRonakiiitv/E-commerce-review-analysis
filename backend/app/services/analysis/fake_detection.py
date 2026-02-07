"""Fake review detection service."""
import re
from datetime import datetime
from typing import Dict, List
from collections import Counter

from sqlalchemy.orm import Session

from app.models import Review


# Generic/suspicious phrases
GENERIC_PHRASES = [
    "good product", "nice product", "best product", "worst product",
    "highly recommend", "do not buy", "waste of money", "value for money",
    "must buy", "don't buy", "excellent", "terrible", "amazing", "horrible",
    "five stars", "one star", "5 stars", "1 star"
]


def calculate_suspicious_score(review: Review) -> int:
    """
    Calculate a suspicion score for a review (0-100).
    Higher score = more suspicious.
    """
    score = 0
    text = review.review_text.lower()
    word_count = len(text.split())
    
    # 1. Short reviews with extreme ratings (30 points)
    if word_count < 10 and review.rating in [1, 5]:
        score += 30
    elif word_count < 20 and review.rating in [1, 5]:
        score += 15
    
    # 2. Unverified purchase (25 points)
    if not review.verified_purchase:
        score += 25
    
    # 3. Generic phrases (20 points max)
    generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase in text)
    score += min(20, generic_count * 5)
    
    # 4. All caps or excessive punctuation (15 points)
    caps_ratio = sum(1 for c in review.review_text if c.isupper()) / max(len(review.review_text), 1)
    if caps_ratio > 0.5:
        score += 10
    
    exclamation_count = review.review_text.count('!')
    if exclamation_count > 3:
        score += 5
    
    # 5. Extremely short (10 points)
    if word_count < 5:
        score += 10
    
    # 6. Perfect rating with very short review (10 points)
    if review.rating == 5 and word_count < 15:
        score += 10
    
    # 7. Contains spam indicators (10 points)
    spam_patterns = [
        r'http[s]?://',  # URLs
        r'\b(seller|shop|store)\s+(is|was)\s+(great|best|good)\b',  # Seller praise
        r'(\d{10}|\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',  # Phone numbers
    ]
    for pattern in spam_patterns:
        if re.search(pattern, text):
            score += 10
            break
    
    return min(100, score)


async def detect_fake_reviews(db: Session, product_id: int) -> Dict:
    """
    Analyze reviews for suspicious patterns.
    
    Returns:
        Dictionary with fake review analysis
    """
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    if not reviews:
        return {
            "product_id": product_id,
            "total_reviews": 0,
            "suspicious_count": 0,
            "suspicious_percent": 0,
            "suspicious_reviews": [],
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    suspicious_reviews = []
    
    # Calculate suspicion score for each review
    for review in reviews:
        score = calculate_suspicious_score(review)
        review.suspicious_score = score
        review.is_suspicious = score >= 50
        
        if review.is_suspicious:
            suspicious_reviews.append({
                "review_id": review.id,
                "text": review.review_text[:200] + "..." if len(review.review_text) > 200 else review.review_text,
                "rating": review.rating,
                "suspicious_score": score,
                "verified_purchase": review.verified_purchase,
                "reasons": get_suspicion_reasons(review, score)
            })
    
    db.commit()
    
    # Sort by suspicion score
    suspicious_reviews.sort(key=lambda x: x["suspicious_score"], reverse=True)
    
    suspicious_count = len(suspicious_reviews)
    
    return {
        "product_id": product_id,
        "total_reviews": len(reviews),
        "suspicious_count": suspicious_count,
        "suspicious_percent": round(suspicious_count / len(reviews) * 100, 1),
        "suspicious_reviews": suspicious_reviews[:10],  # Top 10
        "analyzed_at": datetime.utcnow().isoformat()
    }


def get_suspicion_reasons(review: Review, score: int) -> List[str]:
    """Get human-readable reasons why a review is suspicious."""
    reasons = []
    text = review.review_text.lower()
    word_count = len(text.split())
    
    if not review.verified_purchase:
        reasons.append("Not a verified purchase")
    
    if word_count < 10 and review.rating in [1, 5]:
        reasons.append("Very short review with extreme rating")
    
    generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase in text)
    if generic_count >= 2:
        reasons.append("Contains generic/common phrases")
    
    if word_count < 5:
        reasons.append("Extremely short review")
    
    if re.search(r'http[s]?://', text):
        reasons.append("Contains URLs")
    
    return reasons if reasons else ["Multiple minor suspicious indicators"]


async def check_duplicate_reviews(db: Session, product_id: int) -> List[Dict]:
    """
    Find potential duplicate or templated reviews.
    
    Returns:
        List of suspected duplicate groups
    """
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    if len(reviews) < 10:
        return []
    
    # Simple approach: find reviews with very similar first/last words
    text_groups = {}
    
    for review in reviews:
        words = review.review_text.lower().split()
        if len(words) >= 5:
            # Key based on first and last 3 words
            key = " ".join(words[:3]) + " ... " + " ".join(words[-3:])
            if key not in text_groups:
                text_groups[key] = []
            text_groups[key].append({
                "review_id": review.id,
                "text": review.review_text[:100]
            })
    
    # Find groups with duplicates
    duplicates = []
    for key, group in text_groups.items():
        if len(group) >= 2:
            duplicates.append({
                "pattern": key,
                "count": len(group),
                "reviews": group[:5]
            })
    
    return sorted(duplicates, key=lambda x: x["count"], reverse=True)[:5]
