"""Amazon product review scraper."""
import asyncio
import random
import re
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional
from dateutil import parser as date_parser

import requests
from bs4 import BeautifulSoup
from app.config import get_settings


class AmazonScraper:
    """Scraper for Amazon product reviews."""
    
    def __init__(self):
        self.session = requests.Session()
        self.product_name: Optional[str] = None
        
        # List of potential user agents to rotate
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers to mimic a real browser."""
        ua = random.choice(self.user_agents)
        return {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
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
    
    def _build_reviews_url(self, product_url: str, page: int = 1) -> str:
        """Build the reviews page URL."""
        # Extract ASIN
        # Try multiple patterns for ASIN
        asin_patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})'
        ]
        
        asin = None
        for pattern in asin_patterns:
            match = re.search(pattern, product_url)
            if match:
                asin = match.group(1)
                break
        
        if not asin:
            # Fallback: try to find any 10 char string that looks like an ASIN
            match = re.search(r'([B0][A-Z0-9]{9})', product_url)
            if match:
                asin = match.group(1)
            else:
                raise ValueError("Could not extract ASIN from URL")
        
        # Determine domain
        if ".in" in product_url:
            domain = "www.amazon.in"
        else:
            domain = "www.amazon.com"
        
        return f"https://{domain}/product-reviews/{asin}/ref=cm_cr_arp_d_paging_btm_next_{page}?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber={page}"

    def _build_fallback_url(self, product_url: str) -> str:
        """Build a fallback URL (main product page) if reviews are blocked."""
        # Extract ASIN
        match = re.search(r'([B0][A-Z0-9]{9})', product_url)
        if match:
            asin = match.group(1)
            if ".in" in product_url:
                return f"https://www.amazon.in/dp/{asin}"
            else:
                return f"https://www.amazon.com/dp/{asin}"
        return product_url
    
    def _parse_review(self, review_div: BeautifulSoup) -> Optional[Dict]:
        """Parse a single review div."""
        try:
            # Get review text
            body = review_div.find('span', {'data-hook': 'review-body'})
            if not body:
                return None
            text = body.get_text(strip=True)
            
            if not text or len(text) < 5:
                # Try to get title as text if body is empty
                title = review_div.find('a', {'data-hook': 'review-title'})
                if title:
                    text = title.get_text(strip=True)
                else:
                    return None
            
            # Get rating
            rating_elem = review_div.find('i', {'data-hook': 'review-star-rating'})
            if not rating_elem:
                rating_elem = review_div.find('i', {'data-hook': 'cmps-review-star-rating'})
            
            rating = 3  # default
            if rating_elem:
                rating_text = rating_elem.get_text()
                # "4.0 out of 5 stars" -> 4
                rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                if rating_match:
                    val = float(rating_match.group(1))
                    rating = int(round(val))
            
            # Get date
            date_elem = review_div.find('span', {'data-hook': 'review-date'})
            review_date = None
            if date_elem:
                date_text = date_elem.get_text()
                # Extract date from "Reviewed in India on January 15, 2024"
                date_match = re.search(r'on (.+)$', date_text)
                if date_match:
                    try:
                        review_date = date_parser.parse(date_match.group(1)).date()
                    except:
                        pass
            
            if not review_date:
                review_date = datetime.now().date()
            
            # Get reviewer name
            profile = review_div.find('span', class_='a-profile-name')
            reviewer_name = profile.get_text(strip=True) if profile else "Amazon Customer"
            
            # Check verified purchase
            verified_elem = review_div.find('span', {'data-hook': 'avp-badge'})
            verified = verified_elem is not None
            
            # Get helpful count
            helpful_elem = review_div.find('span', {'data-hook': 'helpful-vote-statement'})
            helpful_count = 0
            if helpful_elem:
                helpful_text = helpful_elem.get_text()
                helpful_match = re.search(r'(\d+)', helpful_text)
                if helpful_match:
                    helpful_count = int(helpful_match.group(1))
                elif "One person" in helpful_text:
                    helpful_count = 1
            
            return {
                'text': text,
                'rating': rating,
                'date': review_date,
                'reviewer_name': reviewer_name,
                'verified': verified,
                'helpful_count': helpful_count
            }
        
        except Exception as e:
            print(f"Error parsing review: {e}")
            return None
    
    async def scrape_reviews(
        self,
        product_url: str,
        max_reviews: int = 50,  # Lower default for safety
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """
        Scrape reviews from Amazon product page.
        """
        reviews = []
        page = 1
        consecutive_empty = 0
        consecutive_errors = 0
        
        print(f"Starting scrape for: {product_url}")
        
        while len(reviews) < max_reviews and consecutive_empty < 3 and consecutive_errors < 5:
            try:
                url = self._build_reviews_url(product_url, page)
                
                # Make request with random delay
                delay = random.uniform(2, 5) # Reasonable delay
                print(f"Scraping page {page} (delay {delay:.1f}s)...")
                await asyncio.sleep(delay)
                
                response = await asyncio.to_thread(
                    self.session.get,
                    url,
                    headers=self._get_headers(),
                    timeout=15
                )
                
                if response.status_code != 200:
                    print(f"Got status {response.status_code} on page {page}")
                    consecutive_errors += 1
                    
                    # If blocked, wait longer and try again
                    if response.status_code in [503, 403, 429]:
                        print("Blocked! Waiting 10 seconds...")
                        await asyncio.sleep(10)
                        # Rotate session
                        self.session = requests.Session()
                        continue
                    
                    page += 1
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for captcha
                if soup.find('input', id='captchacharacters'):
                    print("CAPTCHA detected! Stopping scrape to avoid ban.")
                    break
                
                # Check for "Something went wrong"
                if "Something went wrong" in soup.get_text() or "Serve Protection" in soup.get_text():
                    print("Blocked! (Something went wrong / Serve Protection)")
                    consecutive_errors += 1
                    await asyncio.sleep(10)
                    self.session = requests.Session()
                    continue

                # Get product name on first page
                if page == 1 and not self.product_name:
                    title = soup.find('a', {'data-hook': 'product-link'})
                    if title:
                        self.product_name = title.get_text(strip=True)
                    else:
                        # Fallback title
                        title_tag = soup.find('title')
                        if title_tag:
                            self.product_name = title_tag.get_text(strip=True).replace("Amazon.in:Customer reviews: ", "").replace("Amazon.com:Customer reviews: ", "")
                
                # Find review divs
                review_divs = soup.find_all('div', {'data-hook': 'review'})
                
                if not review_divs:
                    # Check if we hit a different layout
                    alt_divs = soup.find_all('div', class_='a-section review aok-relative')
                    if alt_divs:
                        review_divs = alt_divs

                if not review_divs:
                    print(f"No reviews found on page {page}")
                    
                    # Try fallback if first page fails
                    if page == 1 and consecutive_errors == 0:
                        print("Trying fallback URL...")
                        fallback_url = self._build_fallback_url(product_url)
                        if fallback_url != url:
                            print(f"Scraping fallback: {fallback_url}")
                            try:
                                await asyncio.sleep(random.uniform(2, 5))
                                response = await asyncio.to_thread(self.session.get, fallback_url, headers=self._get_headers(), timeout=15)
                                if response.status_code == 200:
                                    soup_fb = BeautifulSoup(response.content, 'html.parser')
                                    review_divs = soup_fb.find_all('div', {'data-hook': 'review'})
                                    print(f"Fallback found {len(review_divs)} reviews")
                                    if review_divs:
                                        url = fallback_url  # Update current URL context
                                        soup = soup_fb      # Update soup
                            except Exception as e:
                                print(f"Fallback failed: {e}")

                    if not review_divs:
                        consecutive_empty += 1
                        page += 1
                        continue
                
                print(f"Found {len(review_divs)} reviews on page {page}")
                consecutive_empty = 0
                consecutive_errors = 0
                
                for div in review_divs:
                    if len(reviews) >= max_reviews:
                        break
                    
                    review = self._parse_review(div)
                    if review:
                        # Avoid duplicates
                        if not any(r['text'] == review['text'] for r in reviews):
                            reviews.append(review)
                        
                        if progress_callback:
                            progress_callback(len(reviews), max_reviews)
                
                page += 1
                
            except Exception as e:
                print(f"Request error on page {page}: {e}")
                consecutive_errors += 1
                await asyncio.sleep(5)
        
        print(f"Scraping finished. Total reviews: {len(reviews)}")
        return reviews
