"""
Fake review detection service.

Combines a trained ML classifier (TF-IDF + Logistic Regression) with
heuristic scoring for robust fake review detection.

The ML model is trained on a labeled dataset of genuine vs. deceptive
reviews (see app/ml/train_fake_classifier.py for training pipeline and
app/ml/model/metrics.json for evaluation metrics).
"""
import os
import pickle
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from scipy.sparse import hstack, csr_matrix
from sqlalchemy.orm import Session

from app.models import Review

logger = logging.getLogger(__name__)

# ─── Paths ───────────────────────────────────────────────────────────
_ML_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "model"
_MODEL_PATH = _ML_DIR / "fake_classifier.pkl"
_VECTORIZER_PATH = _ML_DIR / "tfidf_vectorizer.pkl"
_METRICS_PATH = _ML_DIR / "metrics.json"

# ─── Lazy-loaded model ───────────────────────────────────────────────
_classifier = None
_tfidf = None
_scaler = None

# Generic/suspicious phrases (shared with training features)
GENERIC_PHRASES = [
    "good product", "nice product", "best product", "worst product",
    "highly recommend", "do not buy", "waste of money", "value for money",
    "must buy", "don't buy", "excellent", "terrible", "amazing", "horrible",
    "five stars", "one star", "5 stars", "1 star",
]


def _load_model():
    """Load the trained classifier and vectorizer."""
    global _classifier, _tfidf, _scaler

    if _classifier is not None:
        return True

    if not _MODEL_PATH.exists() or not _VECTORIZER_PATH.exists():
        logger.warning("Fake-review ML model not found at %s", _ML_DIR)
        logger.warning("Falling back to heuristic scoring only.")
        logger.warning("Run: python -m app.ml.train_fake_classifier")
        return False

    with open(_MODEL_PATH, "rb") as f:
        data = pickle.load(f)
        _classifier = data["classifier"]
        _scaler = data["scaler"]

    with open(_VECTORIZER_PATH, "rb") as f:
        _tfidf = pickle.load(f)

    logger.info("Fake-review ML model loaded")
    return True


def _extract_features(text: str, rating: int, verified: bool) -> List[float]:
    """
    Extract the same 8 handcrafted features used during training.

    Must stay in sync with app/ml/train_fake_classifier.py.
    """
    words = text.split()
    word_count = max(len(words), 1)
    avg_word_len = float(np.mean([len(w) for w in words])) if words else 0.0

    exclamation_ratio = text.count("!") / word_count
    upper_chars = sum(1 for c in text if c.isupper())
    caps_ratio = upper_chars / max(len(text), 1)
    rating_extremity = 1.0 if rating in (1, 5) else 0.0

    text_lower = text.lower()
    generic_count = sum(1 for p in GENERIC_PHRASES if p in text_lower)

    unique_words = set(w.lower().strip(".,!?;:") for w in words)
    unique_ratio = len(unique_words) / word_count
    is_verified = 1.0 if verified else 0.0

    return [
        word_count, avg_word_len, exclamation_ratio, caps_ratio,
        rating_extremity, generic_count, unique_ratio, is_verified,
    ]


def ml_predict(text: str, rating: int, verified: bool) -> Optional[Dict]:
    """
    Get ML model prediction for a single review.

    Returns:
        {"label": 0|1, "probability": float} or None if model unavailable.
    """
    if not _load_model():
        return None

    tfidf_vec = _tfidf.transform([text])
    hc = np.array([_extract_features(text, rating, verified)])
    hc_scaled = _scaler.transform(hc)
    X = hstack([tfidf_vec, csr_matrix(hc_scaled)])

    label = int(_classifier.predict(X)[0])
    proba = float(_classifier.predict_proba(X)[0][label])

    return {"label": label, "probability": proba}


# ─── Heuristic scoring (secondary signal) ────────────────────────────

def calculate_heuristic_score(text: str, rating: int, verified: bool) -> int:
    """
    Rule-based suspicion score (0–100).  Used as fallback & secondary signal.
    """
    score = 0
    text_lower = text.lower()
    word_count = len(text_lower.split())

    if word_count < 10 and rating in (1, 5):
        score += 30
    elif word_count < 20 and rating in (1, 5):
        score += 15
    if not verified:
        score += 25
    generic_count = sum(1 for p in GENERIC_PHRASES if p in text_lower)
    score += min(20, generic_count * 5)
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if caps_ratio > 0.5:
        score += 10
    if text.count("!") > 3:
        score += 5
    if word_count < 5:
        score += 10
    if rating == 5 and word_count < 15:
        score += 10
    spam_patterns = [
        r"http[s]?://",
        r"\b(seller|shop|store)\s+(is|was)\s+(great|best|good)\b",
        r"(\d{10}|\d{3}[-.\s]?\d{3}[-.\s]?\d{4})",
    ]
    for p in spam_patterns:
        if re.search(p, text_lower):
            score += 10
            break

    return min(100, score)


def calculate_suspicious_score(review: Review) -> int:
    """
    Combined suspicion score for a Review ORM object.

    Uses ML prediction (70% weight) + heuristic (30% weight).
    Falls back to heuristic-only when model is unavailable.
    """
    text = review.review_text
    rating = review.rating
    verified = review.verified_purchase

    heuristic = calculate_heuristic_score(text, rating, verified)

    ml_result = ml_predict(text, rating, verified)
    if ml_result is not None:
        ml_score = (
            int(ml_result["probability"] * 100) if ml_result["label"] == 1
            else int((1 - ml_result["probability"]) * 100)
        )
        combined = int(0.7 * ml_score + 0.3 * heuristic)
        return min(100, combined)

    return heuristic


async def detect_fake_reviews(db: Session, product_id: int) -> Dict:
    """
    Analyze reviews for suspicious / fake patterns.

    Returns aggregated results including ML confidence and heuristic reasons.
    """
    reviews = db.query(Review).filter(Review.product_id == product_id).all()

    if not reviews:
        return {
            "product_id": product_id,
            "total_reviews": 0,
            "suspicious_count": 0,
            "suspicious_percent": 0,
            "suspicious_reviews": [],
            "model_available": _load_model(),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    suspicious_reviews = []

    for review in reviews:
        score = calculate_suspicious_score(review)
        review.suspicious_score = score
        review.is_suspicious = score >= 50

        if review.is_suspicious:
            ml_result = ml_predict(
                review.review_text, review.rating, review.verified_purchase
            )
            suspicious_reviews.append({
                "review_id": review.id,
                "text": (review.review_text[:200] + "...")
                    if len(review.review_text) > 200 else review.review_text,
                "rating": review.rating,
                "suspicious_score": score,
                "ml_prediction": ml_result,
                "verified_purchase": review.verified_purchase,
                "reasons": get_suspicion_reasons(
                    review.review_text, review.rating, review.verified_purchase, score
                ),
            })

    db.commit()

    suspicious_reviews.sort(key=lambda x: x["suspicious_score"], reverse=True)
    suspicious_count = len(suspicious_reviews)

    return {
        "product_id": product_id,
        "total_reviews": len(reviews),
        "suspicious_count": suspicious_count,
        "suspicious_percent": round(suspicious_count / len(reviews) * 100, 1),
        "suspicious_reviews": suspicious_reviews[:10],
        "model_available": _load_model(),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def get_suspicion_reasons(
    text: str, rating: int, verified: bool, score: int
) -> List[str]:
    """Human-readable reasons why a review was flagged."""
    reasons = []
    text_lower = text.lower()
    word_count = len(text_lower.split())

    if not verified:
        reasons.append("Not a verified purchase")
    if word_count < 10 and rating in (1, 5):
        reasons.append("Very short review with extreme rating")
    generic_count = sum(1 for p in GENERIC_PHRASES if p in text_lower)
    if generic_count >= 2:
        reasons.append("Contains generic/common phrases")
    if word_count < 5:
        reasons.append("Extremely short review")
    if re.search(r"http[s]?://", text_lower):
        reasons.append("Contains URLs")

    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if caps_ratio > 0.5:
        reasons.append("Excessive use of capital letters")

    ml_result = ml_predict(text, rating, verified)
    if ml_result and ml_result["label"] == 1:
        reasons.append(
            f"ML classifier: {ml_result['probability']:.0%} confidence fake"
        )

    return reasons if reasons else ["Multiple minor suspicious indicators"]


async def check_duplicate_reviews(db: Session, product_id: int) -> List[Dict]:
    """Find potential duplicate or templated reviews."""
    reviews = db.query(Review).filter(Review.product_id == product_id).all()

    if len(reviews) < 10:
        return []

    text_groups: Dict[str, list] = {}

    for review in reviews:
        words = review.review_text.lower().split()
        if len(words) >= 5:
            key = " ".join(words[:3]) + " ... " + " ".join(words[-3:])
            text_groups.setdefault(key, []).append({
                "review_id": review.id,
                "text": review.review_text[:100],
            })

    duplicates = [
        {"pattern": key, "count": len(group), "reviews": group[:5]}
        for key, group in text_groups.items()
        if len(group) >= 2
    ]
    return sorted(duplicates, key=lambda x: x["count"], reverse=True)[:5]


def get_model_metrics() -> Optional[Dict]:
    """
    Load saved evaluation metrics from disk.

    Returns None if the model hasn't been trained yet.
    """
    if not _METRICS_PATH.exists():
        return None
    import json
    with open(_METRICS_PATH) as f:
        return json.load(f)
