"""Base scraper with common functionality and platform routing."""
import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Callable, Optional, Tuple
from urllib.parse import urlparse

from app.database import SessionLocal
from app.models import Product, Review

logger = logging.getLogger(__name__)


def detect_platform(url: str) -> str:
    """Detect e-commerce platform from URL. Only Flipkart is supported."""
    domain = urlparse(url).netloc.lower()
    if "flipkart" in domain:
        return "flipkart"
    else:
        raise ValueError(f"Unsupported platform: {domain}. Only Flipkart URLs are supported.")


def clean_product_url(url: str, platform: str) -> str:
    """Extract and clean the Flipkart product URL."""
    if platform == "flipkart":
        # Clean Flipkart URL – strip tracking / query params
        parsed = urlparse(url)
        return f"https://www.flipkart.com{parsed.path}"
    return url


def _use_lightweight_scraper() -> bool:
    """Check if we should skip Playwright and use HTTP-only scraping.

    Enabled by default on Render / Docker deployments where Chromium is too
    heavy or cloud IPs are blocked by Flipkart.
    """
    flag = os.environ.get("LIGHTWEIGHT_SCRAPER", "").lower()
    if flag in ("1", "true", "yes"):
        return True
    # Auto-detect Render environment
    if os.environ.get("RENDER"):
        return True
    return False


async def _scrape_with_http(clean_url, max_reviews, update_progress):
    """Scrape using the lightweight HTTP-based scraper."""
    from app.services.scraper.flipkart_http import FlipkartHTTPScraper

    scraper = FlipkartHTTPScraper()
    reviews_data = await scraper.scrape_reviews_with_retry(
        clean_url,
        max_reviews=max_reviews,
        progress_callback=update_progress,
    )
    return scraper, reviews_data


async def _scrape_with_playwright(clean_url, max_reviews, update_progress):
    """Scrape using the Playwright browser-based scraper."""
    from app.services.scraper.flipkart import FlipkartScraper

    scraper = FlipkartScraper()
    reviews_data = await scraper.scrape_reviews_with_retry(
        clean_url,
        max_reviews=max_reviews,
        progress_callback=update_progress,
    )
    return scraper, reviews_data


async def scrape_product(
    url: str,
    max_reviews: int = 200,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Tuple[int, int]:
    """
    Scrape a Flipkart product and its reviews.

    Strategy selection:
    - **Deployment (Render)**: Uses HTTP-only scraper (low RAM, no Chromium).
    - **Local development**: Tries Playwright first, falls back to HTTP scraper.

    Args:
        url: Flipkart product URL
        max_reviews: Maximum number of reviews to scrape
        progress_callback: Callback function(progress_percent, reviews_count)

    Returns:
        Tuple of (product_id, reviews_count)
    """
    platform = detect_platform(url)
    clean_url = clean_product_url(url, platform)

    db = SessionLocal()

    try:
        # Check if product already exists
        existing = db.query(Product).filter(Product.url == clean_url).first()
        if existing:
            product = existing
        else:
            product = Product(url=clean_url, platform=platform)
            db.add(product)
            db.commit()
            db.refresh(product)

        # Define progress wrapper
        def update_progress(current: int, total: int):
            if progress_callback:
                percent = int((current / total) * 100) if total > 0 else 0
                progress_callback(percent, current)

        lightweight = _use_lightweight_scraper()
        scraper = None
        reviews_data = []

        if lightweight:
            # ── Deployment path: HTTP-only ──
            logger.info("Using lightweight HTTP scraper (LIGHTWEIGHT_SCRAPER=true)")
            scraper, reviews_data = await _scrape_with_http(
                clean_url, max_reviews, update_progress
            )
        else:
            # ── Local path: Playwright → HTTP fallback ──
            logger.info("Trying Playwright scraper (local mode)...")
            try:
                scraper, reviews_data = await _scrape_with_playwright(
                    clean_url, max_reviews, update_progress
                )
            except Exception as pw_err:
                logger.warning(
                    "Playwright scraper failed: %s — falling back to HTTP scraper",
                    pw_err,
                )

            if not reviews_data:
                logger.info("Falling back to HTTP scraper...")
                scraper, reviews_data = await _scrape_with_http(
                    clean_url, max_reviews, update_progress
                )

        if not reviews_data:
            # Clean up the empty product so we don't leave ghost entries
            if not existing:
                db.delete(product)
                db.commit()
            raise RuntimeError(
                "Scraper collected 0 reviews. Flipkart may have shown a CAPTCHA, "
                "the product may have no reviews, or the page layout changed. "
                "Please try again in a minute."
            )

        # Update product info
        if reviews_data:
            product.name = getattr(scraper, "product_name", None) or product.name
            product.total_reviews = len(reviews_data)
            product.scraped_at = datetime.now(timezone.utc)

            # Calculate average rating
            ratings = [r['rating'] for r in reviews_data if r.get('rating')]
            if ratings:
                product.avg_rating = sum(ratings) / len(ratings)

        # Delete old reviews and add new ones
        db.query(Review).filter(Review.product_id == product.id).delete()

        for review_data in reviews_data:
            review = Review(
                product_id=product.id,
                review_text=review_data.get('text', ''),
                rating=review_data.get('rating', 3),
                review_date=review_data.get('date'),
                reviewer_name=review_data.get('reviewer_name'),
                verified_purchase=review_data.get('verified', False),
                helpful_count=review_data.get('helpful_count', 0)
            )
            db.add(review)

        db.commit()

        # Free scraper memory before heavy analysis
        import gc
        gc.collect()

        # Run initial analysis
        from app.services.analysis import run_complete_analysis
        await run_complete_analysis(product.id)

        return product.id, len(reviews_data)

    finally:
        db.close()
