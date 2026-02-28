"""Shared test fixtures for the review analyzer test suite."""
import os
import sys
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override DB URL *before* any app code is imported
os.environ["DATABASE_URL"] = "sqlite://"

from app.database import Base, get_db  # noqa: E402
from app.models import Product, Review, ReviewAspect, AnalysisCache, Topic  # noqa: E402

# In-memory SQLite (no file to clean up)
TEST_DATABASE_URL = "sqlite://"
test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# ────────────────────────────── Fixtures ──────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db():
    """Provide a clean database session per test (rolls back after each)."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSession(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def sample_product(db):
    """Insert a sample product and return it."""
    product = Product(
        name="Test Smartphone XYZ",
        url="https://www.flipkart.com/test-smartphone-xyz/p/itm123",
        platform="flipkart",
        total_reviews=5,
        avg_rating=4.0,
        scraped_at=datetime.now(timezone.utc),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture()
def sample_reviews(db, sample_product):
    """Insert a diverse set of reviews."""
    reviews_data = [
        {
            "review_text": (
                "Excellent phone with a brilliant display and smooth performance. "
                "The battery lasts all day and the camera quality is amazing. "
                "Highly recommend this phone for anyone looking for a flagship experience."
            ),
            "rating": 5,
            "verified_purchase": True,
            "reviewer_name": "Alice",
        },
        {
            "review_text": (
                "Delivery was very slow and the packaging was damaged. "
                "The screen had a scratch out of the box. "
                "Very disappointed with the service."
            ),
            "rating": 1,
            "verified_purchase": True,
            "reviewer_name": "Bob",
        },
        {
            "review_text": "Good product. Nice quality.",
            "rating": 5,
            "verified_purchase": False,
            "reviewer_name": "Charlie",
        },
        {
            "review_text": (
                "Average phone for the price. Nothing special about the camera "
                "but the battery is decent. Design is okay."
            ),
            "rating": 3,
            "verified_purchase": True,
            "reviewer_name": "Diana",
        },
        {
            "review_text": "BEST PRODUCT EVER!!! BUY NOW!!! AMAZING!!!",
            "rating": 5,
            "verified_purchase": False,
            "reviewer_name": "Spammer",
        },
    ]

    reviews = []
    for data in reviews_data:
        review = Review(product_id=sample_product.id, **data)
        db.add(review)
        reviews.append(review)

    db.commit()
    for r in reviews:
        db.refresh(r)
    return reviews


@pytest.fixture()
def app_client(db):
    """Create a FastAPI TestClient with the test database session."""
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from app.main import app

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    # Patch get_db dependency
    app.dependency_overrides[get_db] = _override_get_db

    # Also patch SessionLocal used directly by /api/stats and runner
    with patch("app.database.SessionLocal", lambda: db):
        client = TestClient(app, raise_server_exceptions=False)
        yield client

    app.dependency_overrides.clear()
