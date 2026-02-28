"""Unit tests for the insights aggregation service.

Tests cover:
- Common keyword extraction  (extract_common_keywords)
"""
import pytest
from unittest.mock import MagicMock
from app.services.analysis.insights import extract_common_keywords


class TestExtractCommonKeywords:
    """Tests for the keyword extraction helper."""

    @staticmethod
    def _make_reviews(texts, label="positive"):
        """Create lightweight mock Review objects."""
        reviews = []
        for text in texts:
            r = MagicMock()
            r.review_text = text
            r.sentiment_label = label
            reviews.append(r)
        return reviews

    def test_returns_list(self):
        reviews = self._make_reviews([
            "Excellent battery life and great camera quality",
            "Battery is superb and screen is bright",
        ])
        keywords = extract_common_keywords(reviews, positive=True)
        assert isinstance(keywords, list)

    def test_top_n_limit(self):
        reviews = self._make_reviews([
            "Excellent battery life and great camera quality for the price range",
            "Battery backup is superb and display is bright and vivid",
            "Great performance smooth experience fast charging battery lasts long",
        ])
        keywords = extract_common_keywords(reviews, positive=True, top_n=5)
        assert len(keywords) <= 5

    def test_empty_reviews(self):
        keywords = extract_common_keywords([], positive=True)
        assert isinstance(keywords, list)
        assert len(keywords) == 0

    def test_negative_keywords(self):
        reviews = self._make_reviews(
            [
                "Terrible battery life, keeps draining",
                "Very slow performance, lag everywhere",
                "Worst camera quality, blurry photos",
            ],
            label="negative",
        )
        keywords = extract_common_keywords(reviews, positive=False)
        assert isinstance(keywords, list)
