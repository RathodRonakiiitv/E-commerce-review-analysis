"""Unit tests for topic modeling service.

Tests cover:
- Text preprocessing     (preprocess_text)
- LDA topic modeling     (run_lda)
- Topic label generation (generate_topic_label)
"""
import pytest
from app.services.analysis.topics import preprocess_text, run_lda, generate_topic_label


class TestPreprocessText:
    """Tests for the text preprocessing utility."""

    def test_lowercases(self):
        tokens = preprocess_text("GREAT Phone Design")
        assert all(t == t.lower() for t in tokens)

    def test_removes_stopwords(self):
        tokens = preprocess_text("I have a very good phone that is nice")
        assert "i" not in tokens
        assert "a" not in tokens
        assert "very" not in tokens
        assert "is" not in tokens

    def test_removes_short_words(self):
        tokens = preprocess_text("ok go do it me by")
        # All words are <= 2 chars or stopwords → empty list
        assert all(len(t) > 2 for t in tokens)

    def test_removes_special_characters(self):
        tokens = preprocess_text("Great! Phone @#$% works 100%")
        for token in tokens:
            assert token.isalpha()

    def test_empty_input(self):
        assert preprocess_text("") == []

    def test_returns_meaningful_tokens(self):
        tokens = preprocess_text(
            "The battery performance and camera quality are outstanding"
        )
        assert "battery" in tokens
        assert "performance" in tokens
        assert "camera" in tokens
        assert "quality" in tokens
        assert "outstanding" in tokens


class TestRunLDA:
    """Tests for the Gensim LDA implementation."""

    @pytest.fixture()
    def sample_documents(self):
        """Return preprocessed documents for topic modeling."""
        texts = [
            "battery life is excellent lasts all day long charge quickly",
            "battery drain too fast need charging every few hours",
            "camera quality amazing photos clear sharp low light decent",
            "camera photos blurry front selfie bad rear camera good",
            "screen display bright colors vivid amoled panel quality",
            "display resolution sharp brightness outdoor visibility good",
            "battery backup good overnight drain minimal power efficient",
            "camera zoom optical lens portrait mode excellent photos",
            "display scratch resistant gorilla glass protection clear",
            "battery charge fast wireless charging supported type usb",
            "screen touch responsive smooth scrolling gaming display",
            "camera night mode improved compared previous generation",
        ]
        return [preprocess_text(t) for t in texts]

    def test_returns_expected_topic_count(self, sample_documents):
        topics = run_lda(sample_documents, num_topics=3)
        assert len(topics) <= 3

    def test_topic_structure(self, sample_documents):
        topics = run_lda(sample_documents, num_topics=3)
        for topic in topics:
            assert "keywords" in topic
            assert "doc_count" in topic
            assert isinstance(topic["keywords"], list)
            assert len(topic["keywords"]) > 0
            assert topic["doc_count"] >= 2

    def test_empty_documents(self):
        topics = run_lda([], num_topics=3)
        assert topics == []


class TestGenerateTopicLabel:
    """Tests for topic label generation."""

    def test_battery_keywords(self):
        label = generate_topic_label(["battery", "charge", "power"])
        assert "battery" in label.lower()

    def test_camera_keywords(self):
        label = generate_topic_label(["camera", "photo", "lens"])
        assert "camera" in label.lower()

    def test_display_keywords(self):
        label = generate_topic_label(["display", "screen", "brightness"])
        assert "display" in label.lower()

    def test_unknown_keyword_fallback(self):
        label = generate_topic_label(["randomword", "otherword"])
        assert "randomword" in label.lower()
        assert "Related" in label
