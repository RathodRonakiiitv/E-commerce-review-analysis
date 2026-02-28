"""Integration tests for the FastAPI application.

Tests cover:
- Health & stats endpoints
- Product CRUD via API
- Analysis endpoints (sentiment, aspects, topics, insights)
- Model metrics endpoint
"""
import pytest
from app.models import Product, Review


# ─── Health & stats ───────────────────────────────────────────────────

class TestHealth:
    """Smoke tests for the health and stats endpoints."""

    def test_health_check(self, app_client):
        resp = app_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_stats_endpoint(self, app_client, db):
        resp = app_client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_products" in data
        assert "total_reviews" in data


# ─── Products ─────────────────────────────────────────────────────────

class TestProducts:
    """Integration tests for product-related endpoints."""

    def test_list_products_empty(self, app_client):
        resp = app_client.get("/api/products/")
        assert resp.status_code == 200

    def test_get_product_not_found(self, app_client):
        resp = app_client.get("/api/products/99999")
        assert resp.status_code == 404


# ─── Analysis endpoints ──────────────────────────────────────────────

class TestAnalysis:
    """Integration tests for analysis endpoints.

    These require a product with reviews in the test database.
    The fixtures from conftest.py inject sample data.
    """

    def test_sentiment_no_product(self, app_client):
        resp = app_client.get("/api/products/99999/sentiment")
        assert resp.status_code == 404

    def test_aspects_no_product(self, app_client):
        resp = app_client.get("/api/products/99999/aspects")
        assert resp.status_code == 404

    def test_topics_no_product(self, app_client):
        resp = app_client.get("/api/products/99999/topics")
        assert resp.status_code == 404

    def test_insights_no_product(self, app_client):
        resp = app_client.get("/api/products/99999/insights")
        assert resp.status_code == 404

    def test_sentiment_with_product(self, app_client, sample_product, sample_reviews):
        resp = app_client.get(f"/api/products/{sample_product.id}/sentiment")
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == sample_product.id
        assert "overall_score" in data
        assert "distribution" in data
        assert data["total_reviews"] > 0

    def test_aspects_with_product(self, app_client, sample_product, sample_reviews):
        resp = app_client.get(f"/api/products/{sample_product.id}/aspects")
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == sample_product.id
        assert "aspects" in data

    def test_topics_with_product(self, app_client, sample_product, sample_reviews):
        resp = app_client.get(f"/api/products/{sample_product.id}/topics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == sample_product.id
        assert "topics" in data

    def test_insights_with_product(self, app_client, sample_product, sample_reviews):
        resp = app_client.get(f"/api/products/{sample_product.id}/insights")
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == sample_product.id
        assert "overall_score" in data
        assert "rating_distribution" in data


# ─── Model metrics ────────────────────────────────────────────────────

class TestModelMetrics:
    """Integration test for the /model/metrics endpoint."""

    def test_model_metrics_available(self, app_client):
        resp = app_client.get("/api/products/model/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "cross_validation" in data
        cv = data["cross_validation"]
        assert "accuracy" in cv
        assert "precision" in cv
        assert "recall" in cv
        assert "f1_score" in cv


# ─── Reanalyze ────────────────────────────────────────────────────────

class TestReanalyze:
    """Integration tests for the reanalyze endpoint."""

    def test_reanalyze_not_found(self, app_client):
        resp = app_client.post("/api/products/99999/reanalyze")
        assert resp.status_code == 404

    def test_reanalyze_success(self, app_client, sample_product, sample_reviews):
        """Reanalyze triggers a background task which uses its own session.
        We verify the endpoint returns 200 with the right product_id.
        The background task may fail due to the test DB isolation, which is expected."""
        resp = app_client.post(f"/api/products/{sample_product.id}/reanalyze")
        # The endpoint returns 200 immediately before the background task runs
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == sample_product.id
