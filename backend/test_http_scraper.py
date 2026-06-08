"""Quick test for the HTTP-based Flipkart scraper."""
import asyncio
import os
import sys
import logging

# Enable lightweight scraper
os.environ["LIGHTWEIGHT_SCRAPER"] = "true"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.scraper.flipkart_http import FlipkartHTTPScraper


async def main():
    scraper = FlipkartHTTPScraper()
    url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4"
    
    print(f"\nTesting HTTP scraper with URL:\n  {url}\n")
    
    reviews = await scraper.scrape_reviews(url, max_reviews=15)
    
    print(f"\n{'='*60}")
    print(f"Result: {len(reviews)} reviews collected")
    print(f"Product name: {scraper.product_name}")
    print(f"{'='*60}\n")
    
    for i, r in enumerate(reviews[:10], 1):
        text_preview = r["text"][:80] + ("..." if len(r["text"]) > 80 else "")
        # Safely print without unicode errors
        safe_text = text_preview.encode('ascii', 'ignore').decode('ascii')
        safe_name = str(r['reviewer_name']).encode('ascii', 'ignore').decode('ascii')
        print(f"  {i}. [{r['rating']}*] {safe_text}")
        print(f"     By: {safe_name} | Verified: {r['verified']} | Date: {r['date']}")
    
    if len(reviews) > 10:
        print(f"  ... and {len(reviews) - 10} more")
    
    return len(reviews)


if __name__ == "__main__":
    count = asyncio.run(main())
    sys.exit(0 if count > 0 else 1)
