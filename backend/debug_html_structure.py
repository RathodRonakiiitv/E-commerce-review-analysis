"""Dump raw HTML from Flipkart review page to analyze structure."""
import asyncio
import os
import sys
import httpx
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

async def main():
    url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/product-reviews/itm6ac6485515ae4?marketplace=FLIPKART&page=1"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        # Establish session
        headers = {
            "User-Agent": _USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
        }
        await client.get("https://www.flipkart.com", headers=headers)
        
        # Get review page
        headers["Referer"] = "https://www.flipkart.com"
        resp = await client.get(url, headers=headers)
        html = resp.text
        
        # Save raw HTML
        with open("debug_review_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved {len(html)} chars to debug_review_page.html")
        
        # Analyze structure
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        # Count "Certified Buyer" occurrences
        cb_nodes = soup.find_all(string=lambda t: t and "Certified Buyer" in t)
        print(f"'Certified Buyer' occurrences: {len(cb_nodes)}")
        
        # Look for review-like text patterns
        # Check for star rating elements
        star_divs = soup.find_all(string=lambda t: t and t.strip() in ("1","2","3","4","5"))
        print(f"Potential rating elements: {len(star_divs)}")
        
        # Check for "READ MORE" or "Read full review"
        read_more = soup.find_all(string=lambda t: t and ("READ MORE" in t or "Read full review" in t or "READ MORE" in t.upper()))
        print(f"'READ MORE' elements: {len(read_more)}")
        
        # Look for review containers by examining div structure
        # Find all divs with substantial text content
        review_candidates = []
        for div in soup.find_all("div"):
            text = div.get_text(strip=True)
            strings = list(div.stripped_strings)
            # Review containers typically have 4-15 text elements
            if 4 <= len(strings) <= 15 and len(text) > 50:
                # Check if it has a rating-like first element
                if strings[0] in ("1","2","3","4","5") or "Certified Buyer" in text:
                    review_candidates.append(strings)
        
        print(f"\nReview-like containers found: {len(review_candidates)}")
        for i, strings in enumerate(review_candidates[:5]):
            preview = " | ".join(s[:40] for s in strings[:6])
            print(f"  {i+1}. [{len(strings)} strings] {preview}")
        
        # Also check for specific class patterns Flipkart uses
        # Look at divs containing review text patterns
        all_divs_with_text = soup.find_all("div", attrs={"class": True})
        long_text_divs = []
        for d in all_divs_with_text:
            direct_text = d.find(string=True, recursive=False)
            if direct_text and len(direct_text.strip()) > 30:
                long_text_divs.append(direct_text.strip()[:80])
        
        print(f"\nDivs with long direct text: {len(long_text_divs)}")
        for t in long_text_divs[:10]:
            print(f"  - {t}")


if __name__ == "__main__":
    asyncio.run(main())
