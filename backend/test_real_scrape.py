import asyncio
from app.services.scraper.amazon import AmazonScraper

async def test():
    scraper = AmazonScraper()
    url = "https://www.amazon.in/OnePlus-Charcoal-Snapdragon-Personalised-Game-Changing/dp/B0FZSXYV6K"
    print(f"Testing scraper with URL: {url}")
    
    reviews = await scraper.scrape_reviews(url, max_reviews=10)
    
    print(f"\nScraped {len(reviews)} reviews")
    if reviews:
        print(f"Product Name: {scraper.product_name}")
        print("\nSample Review:")
        print(reviews[0])
    else:
        print("Failed to scrape any reviews.")

if __name__ == "__main__":
    asyncio.run(test())
