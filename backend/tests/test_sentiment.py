"""Unit tests for sentiment analysis service.

Tests cover:
- Single text analysis  (analyze_text)
- Batch text analysis   (analyze_texts_batch)
- Edge cases            (empty/very short inputs)
"""
import pytest
from app.services.analysis.sentiment import analyze_text, analyze_texts_batch


class TestAnalyzeText:
    """Tests for the single-text sentiment analyser."""

    def test_positive_text(self):
        label, score = analyze_text(
            "This phone is absolutely wonderful and I love everything about it."
        )
        assert label == "positive"
        assert 0.0 < score <= 1.0

    def test_negative_text(self):
        label, score = analyze_text(
            "Terrible product, stopped working after two days. Total waste of money."
        )
        assert label == "negative"
        assert 0.0 < score <= 1.0

    def test_empty_text_returns_neutral(self):
        label, score = analyze_text("")
        assert label == "neutral"
        assert score == 0.5

    def test_very_short_text_returns_neutral(self):
        label, score = analyze_text("ok")
        assert label == "neutral"
        assert score == 0.5

    def test_long_text_truncated_gracefully(self):
        """Texts longer than 512 chars should not crash."""
        long_text = "I love this phone. " * 200  # ~3800 chars
        label, score = analyze_text(long_text)
        assert label in ("positive", "negative", "neutral")
        assert 0.0 <= score <= 1.0

    def test_returns_tuple(self):
        result = analyze_text("A decent phone for the price.")
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestAnalyzeTextsBatch:
    """Tests for the batch sentiment analyser."""

    def test_batch_returns_same_length(self):
        texts = [
            "Great product!",
            "Terrible quality.",
            "It is okay, nothing special.",
        ]
        results = analyze_texts_batch(texts)
        assert len(results) == len(texts)

    def test_batch_element_structure(self):
        results = analyze_texts_batch(["Good phone", "Bad phone"])
        for label, score in results:
            assert label in ("positive", "negative", "neutral")
            assert 0.0 <= score <= 1.0

    def test_empty_batch(self):
        results = analyze_texts_batch([])
        assert results == []

    def test_batch_with_empty_strings(self):
        results = analyze_texts_batch(["", "Good phone", ""])
        assert len(results) == 3
