"""Unit tests for the fake review detection service.

Tests cover:
- ML model loading and prediction
- Heuristic scoring logic
- Combined scoring (ML + heuristic)
- Suspicion reason generation
- Model metrics retrieval
"""
import pytest
from app.services.analysis.fake_detection import (
    ml_predict,
    calculate_heuristic_score,
    calculate_suspicious_score,
    get_suspicion_reasons,
    get_model_metrics,
    _load_model,
    GENERIC_PHRASES,
)


# ─── ML model tests ──────────────────────────────────────────────────

class TestMLPredict:
    """Tests for the ML classifier predictions."""

    def test_model_loads(self):
        """Model artifacts should be loadable from disk."""
        assert _load_model() is True

    def test_genuine_review_predicted_genuine(self):
        """A detailed, verified, moderate-rating review should be genuine."""
        result = ml_predict(
            "I have been using this phone for three weeks. The camera takes "
            "decent photos in daylight but struggles in low light. Battery "
            "lasts about a day with moderate usage. Build quality feels solid "
            "and the display is bright enough for outdoor use.",
            rating=4,
            verified=True,
        )
        assert result is not None
        assert result["label"] == 0  # genuine
        assert result["probability"] > 0.5

    def test_fake_review_predicted_fake(self):
        """A short, generic, unverified 5-star review should be flagged."""
        result = ml_predict(
            "Best product ever!!! Amazing quality!!!",
            rating=5,
            verified=False,
        )
        assert result is not None
        assert result["label"] == 1  # fake
        assert result["probability"] > 0.5

    def test_returns_dict_with_expected_keys(self):
        result = ml_predict("Some review text here.", rating=3, verified=True)
        assert result is not None
        assert "label" in result
        assert "probability" in result
        assert result["label"] in (0, 1)
        assert 0.0 <= result["probability"] <= 1.0


# ─── Heuristic scoring tests ─────────────────────────────────────────

class TestHeuristicScoring:
    """Tests for the rule-based heuristic scorer."""

    def test_short_extreme_unverified_scores_high(self):
        """Very short, 5-star, unverified review = high suspicion."""
        score = calculate_heuristic_score("Good product!", rating=5, verified=False)
        assert score >= 50

    def test_long_verified_moderate_scores_low(self):
        """Long, verified, moderate review = low suspicion."""
        long_text = (
            "I purchased this phone last month and have been using it daily. "
            "The processor handles multitasking well and the battery easily "
            "lasts through a full workday. Camera is good in daylight but "
            "night mode could be improved. Overall satisfied with the purchase."
        )
        score = calculate_heuristic_score(long_text, rating=4, verified=True)
        assert score < 30

    def test_score_range_0_to_100(self):
        """Score should always be clamped to [0, 100]."""
        # Maximally suspicious input
        score = calculate_heuristic_score(
            "BEST PRODUCT!!! AMAZING!!! BUY NOW!!! http://spam.com "
            "best product ever good product nice product",
            rating=5,
            verified=False,
        )
        assert 0 <= score <= 100

    def test_unverified_adds_penalty(self):
        """Unverified purchase should increase the score."""
        text = "This phone works fine for the price."
        verified_score = calculate_heuristic_score(text, rating=4, verified=True)
        unverified_score = calculate_heuristic_score(text, rating=4, verified=False)
        assert unverified_score > verified_score

    def test_url_adds_penalty(self):
        """Reviews containing URLs should be penalised."""
        base = "Check this great phone deal"
        without_url = calculate_heuristic_score(base, rating=4, verified=True)
        with_url = calculate_heuristic_score(
            base + " https://spam.link", rating=4, verified=True
        )
        assert with_url > without_url

    def test_very_short_review_penalised(self):
        """Extremely short reviews (< 5 words) get extra penalty."""
        score = calculate_heuristic_score("Good phone", rating=5, verified=True)
        assert score > 0


# ─── Combined scoring tests ──────────────────────────────────────────

class TestCombinedScoring:
    """Tests for calculate_suspicious_score (ML + heuristic)."""

    def test_combined_with_review_object(self, db, sample_product, sample_reviews):
        """Combined scoring should work on a Review ORM object."""
        review = sample_reviews[0]  # genuine-looking review
        score = calculate_suspicious_score(review)
        assert 0 <= score <= 100

    def test_suspicious_review_scores_higher(self, db, sample_product, sample_reviews):
        """The spammy review should score higher than the genuine one."""
        genuine = sample_reviews[0]   # detailed, verified, 5-star
        spammy = sample_reviews[4]    # "BEST PRODUCT EVER!!!" unverified
        assert calculate_suspicious_score(spammy) > calculate_suspicious_score(genuine)


# ─── Suspicion reason tests ──────────────────────────────────────────

class TestSuspicionReasons:
    """Tests for get_suspicion_reasons."""

    def test_unverified_flagged(self):
        reasons = get_suspicion_reasons("Average phone", rating=3, verified=False, score=40)
        assert any("verified" in r.lower() for r in reasons)

    def test_short_extreme_flagged(self):
        reasons = get_suspicion_reasons("Great!", rating=5, verified=True, score=50)
        assert any("short" in r.lower() for r in reasons)

    def test_generic_phrases_flagged(self):
        reasons = get_suspicion_reasons(
            "Best product, good product, nice product",
            rating=5, verified=True, score=60,
        )
        assert any("generic" in r.lower() for r in reasons)

    def test_returns_list(self):
        reasons = get_suspicion_reasons("Some text", rating=3, verified=True, score=20)
        assert isinstance(reasons, list)
        assert len(reasons) >= 1  # always at least one reason


# ─── Model metrics tests ─────────────────────────────────────────────

class TestModelMetrics:
    """Tests for get_model_metrics."""

    def test_metrics_available(self):
        """Metrics JSON should be loadable after training."""
        metrics = get_model_metrics()
        assert metrics is not None

    def test_metrics_keys(self):
        """Metrics dict should contain expected evaluation keys."""
        metrics = get_model_metrics()
        assert metrics is not None
        assert "cross_validation" in metrics
        cv = metrics["cross_validation"]
        expected = {"accuracy", "precision", "recall", "f1_score"}
        assert expected.issubset(set(cv.keys()))

    def test_metrics_ranges(self):
        """All metric values should be between 0 and 1."""
        metrics = get_model_metrics()
        cv = metrics["cross_validation"]
        for key in ("accuracy", "precision", "recall", "f1_score"):
            assert 0.0 <= cv[key] <= 1.0, f"{key} out of range"
