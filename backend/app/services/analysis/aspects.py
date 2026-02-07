"""Aspect-based sentiment analysis service."""
import re
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import Review, ReviewAspect
from app.services.analysis.sentiment import analyze_text

# Aspect keywords mapping
ASPECT_KEYWORDS = {
    "quality": [
        "quality", "build", "material", "sturdy", "durable", "cheap", "solid",
        "construction", "craftsmanship", "well-made", "poorly-made", "flimsy"
    ],
    "price": [
        "price", "cost", "expensive", "cheap", "worth", "value", "money",
        "affordable", "overpriced", "budget", "bargain", "deal"
    ],
    "delivery": [
        "delivery", "shipping", "arrived", "package", "packaging", "damaged",
        "late", "early", "on-time", "delayed", "courier", "dispatch"
    ],
    "battery": [
        "battery", "charge", "charging", "lasting", "backup", "drain",
        "power", "mah", "hours", "overnight"
    ],
    "design": [
        "design", "look", "looks", "appearance", "color", "colour", "aesthetic",
        "sleek", "beautiful", "ugly", "style", "stylish", "compact", "slim"
    ],
    "performance": [
        "performance", "speed", "fast", "slow", "lag", "smooth", "responsive",
        "quick", "snappy", "hangs", "freezes", "crash"
    ],
    "camera": [
        "camera", "photo", "photos", "picture", "pictures", "selfie", "video",
        "lens", "zoom", "focus", "blur", "clarity"
    ],
    "display": [
        "display", "screen", "resolution", "brightness", "visibility", "panel",
        "lcd", "amoled", "oled", "hd", "touch"
    ],
    "sound": [
        "sound", "audio", "speaker", "volume", "bass", "music", "loud",
        "clear", "noise", "earphone", "headphone"
    ],
    "customer_service": [
        "service", "support", "response", "help", "complaint", "warranty",
        "return", "refund", "replacement", "customer care"
    ]
}


def extract_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]


def find_aspect_in_text(text: str, aspect: str, keywords: List[str]) -> List[str]:
    """Find sentences mentioning an aspect."""
    text_lower = text.lower()
    sentences = extract_sentences(text)
    
    matching_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for keyword in keywords:
            if keyword in sentence_lower:
                matching_sentences.append(sentence)
                break
    
    return matching_sentences


async def analyze_product_aspects(db: Session, product_id: int) -> Dict:
    """
    Perform aspect-based sentiment analysis.
    
    Returns:
        Dictionary with aspect sentiments
    """
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    if not reviews:
        return {
            "product_id": product_id,
            "aspects": [],
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    # Clear existing aspects
    db.query(ReviewAspect).filter(
        ReviewAspect.review_id.in_([r.id for r in reviews])
    ).delete(synchronize_session=False)
    
    # Aggregate aspect data
    aspect_data = defaultdict(lambda: {
        "positive": 0, "negative": 0, "neutral": 0,
        "total_score": 0, "count": 0,
        "positive_samples": [], "negative_samples": []
    })
    
    for review in reviews:
        for aspect, keywords in ASPECT_KEYWORDS.items():
            matching_sentences = find_aspect_in_text(review.review_text, aspect, keywords)
            
            for sentence in matching_sentences:
                # Analyze sentiment of the specific sentence
                label, score = analyze_text(sentence)
                
                # Store aspect in database
                aspect_record = ReviewAspect(
                    review_id=review.id,
                    aspect_name=aspect,
                    sentiment=label,
                    sentiment_score=score,
                    mentioned_text=sentence[:500]
                )
                db.add(aspect_record)
                
                # Aggregate
                data = aspect_data[aspect]
                data[label] += 1
                data["count"] += 1
                
                if label == "positive":
                    data["total_score"] += score
                    if len(data["positive_samples"]) < 3:
                        data["positive_samples"].append(sentence[:200])
                elif label == "negative":
                    data["total_score"] -= score
                    if len(data["negative_samples"]) < 3:
                        data["negative_samples"].append(sentence[:200])
    
    db.commit()
    
    # Build response
    aspects = []
    for aspect, data in aspect_data.items():
        if data["count"] == 0:
            continue
        
        avg_score = data["total_score"] / data["count"]
        # Normalize to 0-1
        normalized_score = (avg_score + 1) / 2
        
        if normalized_score >= 0.6:
            sentiment_label = "positive"
        elif normalized_score <= 0.4:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        aspects.append({
            "aspect_name": aspect,
            "sentiment_label": sentiment_label,
            "average_score": round(normalized_score, 3),
            "positive_count": data["positive"],
            "negative_count": data["negative"],
            "neutral_count": data["neutral"],
            "total_mentions": data["count"],
            "sample_positive": data["positive_samples"],
            "sample_negative": data["negative_samples"]
        })
    
    # Sort by total mentions
    aspects.sort(key=lambda x: x["total_mentions"], reverse=True)
    
    return {
        "product_id": product_id,
        "aspects": aspects,
        "analyzed_at": datetime.utcnow().isoformat()
    }
