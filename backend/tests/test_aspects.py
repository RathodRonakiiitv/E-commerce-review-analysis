"""Unit tests for aspect-based sentiment analysis.

Tests cover:
- Sentence extraction         (extract_sentences)
- Aspect keyword matching     (find_aspect_in_text)
- Aspect keywords coverage    (ASPECT_KEYWORDS)
"""
import pytest
from app.services.analysis.aspects import (
    extract_sentences,
    find_aspect_in_text,
    ASPECT_KEYWORDS,
)


class TestExtractSentences:
    """Tests for sentence splitting."""

    def test_splits_on_period(self):
        sentences = extract_sentences(
            "The battery is great. Camera could be better. Display is bright."
        )
        assert len(sentences) == 3

    def test_splits_on_exclamation(self):
        sentences = extract_sentences("Amazing phone! Loved it! Will buy again!")
        assert len(sentences) >= 2  # short ones may be filtered

    def test_filters_short_fragments(self):
        sentences = extract_sentences("Good. Ok. The battery life is truly excellent.")
        # "Good" and "Ok" are < 10 chars so they should be filtered
        assert all(len(s) > 10 for s in sentences)

    def test_empty_input(self):
        assert extract_sentences("") == []


class TestFindAspectInText:
    """Tests for keyword-based aspect detection in text."""

    def test_battery_detected(self):
        text = (
            "The battery lasts all day. Camera is average. "
            "Charging speed is fast."
        )
        matches = find_aspect_in_text(text, "battery", ASPECT_KEYWORDS["battery"])
        assert len(matches) >= 1
        assert any("battery" in m.lower() or "charging" in m.lower() for m in matches)

    def test_delivery_detected(self):
        text = "Delivery was very fast. Product arrived in good condition."
        matches = find_aspect_in_text(text, "delivery", ASPECT_KEYWORDS["delivery"])
        assert len(matches) >= 1

    def test_no_match_returns_empty(self):
        text = "The weather is nice today."
        matches = find_aspect_in_text(text, "battery", ASPECT_KEYWORDS["battery"])
        assert matches == []

    def test_case_insensitive_matching(self):
        text = "The CAMERA takes great photos. DISPLAY is very bright."
        matches = find_aspect_in_text(text, "camera", ASPECT_KEYWORDS["camera"])
        assert len(matches) >= 1


class TestAspectKeywords:
    """Tests for the ASPECT_KEYWORDS dictionary completeness."""

    EXPECTED_ASPECTS = [
        "quality", "price", "delivery", "battery", "design",
        "performance", "camera", "display", "sound", "customer_service",
    ]

    def test_all_expected_aspects_present(self):
        for aspect in self.EXPECTED_ASPECTS:
            assert aspect in ASPECT_KEYWORDS, f"Missing aspect: {aspect}"

    def test_each_aspect_has_keywords(self):
        for aspect, keywords in ASPECT_KEYWORDS.items():
            assert isinstance(keywords, list)
            assert len(keywords) >= 3, f"Aspect '{aspect}' has too few keywords"
