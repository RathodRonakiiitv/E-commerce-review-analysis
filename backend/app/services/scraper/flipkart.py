"""Flipkart product review scraper."""
import asyncio
import random
import re
from datetime import datetime
from typing import Callable, Dict, List, Optional
from dateutil import parser as date_parser

import requests
from bs4 import BeautifulSoup

from app.config import get_settings

settings = get_settings()


class FlipkartScraper:
    """Scraper for Flipkart product reviews."""
    
    def __init__(self):
        self.session = requests.Session()
        self.product_name: Optional[str] = None
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers to mimic a real browser."""
        ua = random.choice(self.user_agents)
        return {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def _convert_to_review_url(self, product_url: str) -> str:
        """
        Convert a Flipkart product page URL to the reviews page URL.
        Product: /product-name/p/itmXXX  ->  Reviews: /product-name/product-reviews/itmXXX
        """
        if '/product-reviews/' in product_url:
            return product_url
        if '/p/' in product_url:
            return product_url.replace('/p/', '/product-reviews/')
        return product_url

    def _build_reviews_url(self, product_url: str, page: int = 1) -> str:
        """Build the reviews page URL with pagination."""
        base = self._convert_to_review_url(product_url)
        base = re.sub(r'[?&]page=\d+', '', base)
        if '?' in base:
            return f"{base}&marketplace=FLIPKART&page={page}"
        else:
            return f"{base}?marketplace=FLIPKART&page={page}"

    def _parse_review_from_strings(self, strings: List[str]) -> Optional[Dict]:
        """
        Parse a review from stripped_strings of a review container.
        
        Pattern:
        [0] rating, [1] title, [2] text, [3] READ MORE,
        [4+] name, Certified Buyer, location, date, helpful counts...
        """
        try:
            if len(strings) < 4:
                return None
            
            # Rating
            rating = 3
            try:
                val = int(strings[0])
                if 1 <= val <= 5:
                    rating = val
            except (ValueError, IndexError):
                pass
            
            # Title and text
            title = strings[1] if len(strings) > 1 else ""
            review_text = strings[2] if len(strings) > 2 else ""
            
            if review_text == "READ MORE":
                review_text = title
                title = ""
            
            if title and review_text and title != review_text:
                full_text = f"{title}. {review_text}"
            else:
                full_text = review_text or title
            
            full_text = full_text.replace("READ MORE", "").strip()
            if not full_text or len(full_text) < 3:
                return None
            
            # Metadata
            reviewer_name = "Flipkart Customer"
            review_date = datetime.now().date()
            verified = False
            helpful_count = 0
            
            for i, s in enumerate(strings):
                if s == "Certified Buyer":
                    verified = True
                    if i > 0:
                        name = strings[i - 1]
                        if name != "READ MORE" and not name.isdigit() and len(name) < 40:
                            reviewer_name = name
                
                # Date like "Jan, 2024"
                if "," in s and len(s) < 20 and any(m in s for m in [
                    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                ]):
                    try:
                        d = date_parser.parse(s, fuzzy=True).date()
                        if d <= datetime.now().date():
                            review_date = d
                    except (ValueError, OverflowError):
                        pass
                
                if s == "Permalink" and i >= 2:
                    try:
                        helpful_count = int(strings[i - 2].replace(",", ""))
                    except (ValueError, IndexError):
                        pass
            
            return {
                'text': full_text,
                'rating': rating,
                'date': review_date,
                'reviewer_name': reviewer_name,
                'verified': verified,
                'helpful_count': helpful_count
            }
        except Exception as e:
            print(f"  Parse error: {e}")
            return None

    def _extract_reviews_from_soup(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all reviews from a parsed page."""
        reviews = []
        cbs = soup.find_all(string=lambda t: t and "Certified Buyer" in t)
        
        review_containers = []
        for cb in cbs:
            p = cb.parent
            for _ in range(15):
                if p is None:
                    break
                p = p.parent
                if p and p.name == 'div':
                    inner_cbs = len(p.find_all(string=lambda t: t and "Certified Buyer" in t))
                    if inner_cbs != 1:
                        continue
                    strings = list(p.stripped_strings)
                    # The full review container has: rating + title + text + READ MORE + metadata
                    # It should have 10+ strings and contain review text (READ MORE or rating digit)
                    has_review_text = any("READ MORE" in s for s in strings)
                    has_rating = len(strings) > 0 and strings[0] in ["1", "2", "3", "4", "5"]
                    if (has_review_text or has_rating) and len(strings) >= 8:
                        if p not in review_containers:
                            review_containers.append(p)
                        break
        
        for container in review_containers:
            strings = list(container.stripped_strings)
            review = self._parse_review_from_strings(strings)
            if review:
                reviews.append(review)
        
        return reviews

    def _extract_product_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product name from the page."""
        for selector in ['span.B_NuCI', 'h1.yhB1nd']:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        title = soup.find('title')
        if title:
            text = title.get_text(strip=True)
            text = re.sub(r'\s*Reviews:.*', '', text)
            text = re.sub(r'\s*\|.*', '', text)
            if text and len(text) > 5:
                return text
        return None

    async def scrape_reviews(
        self,
        product_url: str,
        max_reviews: int = 50,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """Scrape reviews from Flipkart product page."""
        reviews = []
        page = 1
        consecutive_empty = 0
        consecutive_errors = 0
        max_pages = 25
        
        print(f"Starting Flipkart scrape for: {product_url}")
        
        if "/search?" in product_url and "/p/" not in product_url and "/product-reviews/" not in product_url:
            print("Detected search URL, finding first product...")
            resolved_url = await self.find_product_url_from_search(product_url)
            if resolved_url:
                product_url = resolved_url
                print(f"Resolved to product URL: {product_url}")
            else:
                print("Could not find product from search URL")
                return []
        
        while len(reviews) < max_reviews and consecutive_empty < 3 and consecutive_errors < 5:
            if page > max_pages:
                print(f"Reached max page limit ({max_pages}). Stopping.")
                break
            
            try:
                url = self._build_reviews_url(product_url, page)
                delay = random.uniform(2.0, 4.0)
                print(f"  Page {page} (delay {delay:.1f}s)...")
                await asyncio.sleep(delay)
                
                response = self.session.get(url, headers=self._get_headers(), timeout=20)
                
                if response.status_code != 200:
                    print(f"  Got status {response.status_code} on page {page}")
                    consecutive_errors += 1
                    page += 1
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                if page == 1 and not self.product_name:
                    self.product_name = self._extract_product_name(soup)
                    if self.product_name:
                        print(f"  Product: {self.product_name}")
                
                page_reviews = self._extract_reviews_from_soup(soup)
                
                if not page_reviews:
                    print(f"  No reviews found on page {page}")
                    consecutive_empty += 1
                    page += 1
                    continue
                
                added = 0
                for review in page_reviews:
                    if len(reviews) >= max_reviews:
                        break
                    if not any(r['text'] == review['text'] for r in reviews):
                        reviews.append(review)
                        added += 1
                
                print(f"  Added {added} reviews from page {page}. Total: {len(reviews)}")
                consecutive_empty = 0
                consecutive_errors = 0
                
                if progress_callback:
                    progress_callback(len(reviews), max_reviews)
                
                page += 1
                
            except Exception as e:
                print(f"  Error on page {page}: {e}")
                consecutive_errors += 1
                await asyncio.sleep(5)
        
        print(f"Scraping finished. Total reviews: {len(reviews)}")
        return reviews

    async def find_product_url_from_search(self, search_url: str) -> Optional[str]:
        """Find the first product URL from a Flipkart search page."""
        print(f"Searching: {search_url}")
        try:
            response = self.session.get(search_url, headers=self._get_headers(), timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            all_links = soup.find_all('a', href=True)
            for a in all_links:
                href = a['href']
                if '/p/' in href and '/product-reviews/' not in href:
                    if "http" not in href:
                        return "https://www.flipkart.com" + href.split('?')[0]
                    return href.split('?')[0]
            return None
        except Exception as e:
            print(f"Error finding URL: {e}")
            return None
