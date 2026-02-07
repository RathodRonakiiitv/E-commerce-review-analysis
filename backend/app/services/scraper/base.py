"""Base scraper with common functionality and platform routing."""
import asyncio
import re
from datetime import datetime
from typing import Callable, Optional, Tuple
from urllib.parse import urlparse

from app.database import SessionLocal
from app.models import Product, Review


def detect_platform(url: str) -> str:
    """Detect e-commerce platform from URL."""
    domain = urlparse(url).netloc.lower()
    if "amazon" in domain:
        return "amazon"
    elif "flipkart" in domain:
        return "flipkart"
    else:
        raise ValueError(f"Unsupported platform: {domain}")


def clean_product_url(url: str, platform: str) -> str:
    """Extract and clean the product URL."""
    if platform == "amazon":
        # Extract ASIN and build clean URL
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if asin_match:
            asin = asin_match.group(1)
            # Determine domain
            if ".in" in url:
                return f"https://www.amazon.in/dp/{asin}"
            else:
                return f"https://www.amazon.com/dp/{asin}"
    elif platform == "flipkart":
        # Clean Flipkart URL - strip all tracking/query params
        # Only the path matters: /product-name/p/itmXXX
        parsed = urlparse(url)
        return f"https://www.flipkart.com{parsed.path}"
    
    return url


async def scrape_product(
    url: str,
    max_reviews: int = 200,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Tuple[int, int]:
    """
    Scrape a product and its reviews.
    
    Args:
        url: Product URL from Amazon or Flipkart
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
        
        # Import platform-specific scraper
        if platform == "amazon":
            from app.services.scraper.amazon import AmazonScraper
            scraper = AmazonScraper()
        else:
            from app.services.scraper.flipkart import FlipkartScraper
            scraper = FlipkartScraper()
        
        # Define progress wrapper
        def update_progress(current: int, total: int):
            if progress_callback:
                percent = int((current / total) * 100) if total > 0 else 0
                progress_callback(percent, current)
        
        # Scrape reviews
        reviews_data = await scraper.scrape_reviews(
            clean_url,
            max_reviews=max_reviews,
            progress_callback=update_progress
        )
        
        # Update product info
        if reviews_data:
            product.name = scraper.product_name
            product.total_reviews = len(reviews_data)
            product.scraped_at = datetime.utcnow()
            
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
        
        # Run initial analysis
        from app.services.analysis import run_complete_analysis
        await run_complete_analysis(product.id)
        
        return product.id, len(reviews_data)
    
    finally:
        db.close()
