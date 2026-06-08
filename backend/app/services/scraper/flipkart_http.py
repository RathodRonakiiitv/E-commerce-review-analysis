"""Lightweight Flipkart scraper using HTTP requests + BeautifulSoup.

This scraper is designed for deployment on resource-constrained environments
(e.g., Render free tier) where Playwright Chromium is too heavy (~500MB+ RAM)
and cloud IPs are often blocked by Flipkart's anti-bot systems.

Strategy order:
  1. Flipkart internal API (JSON review data)
  2. HTTP page scraping with rotating headers
"""
import asyncio
import json
import logging
import random
import re
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

# Realistic User-Agent rotation pool
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
]


class FlipkartHTTPScraper:
    """
    Lightweight Flipkart review scraper using HTTP requests.

    Memory footprint: ~20MB vs ~500MB+ for Playwright.
    """

    def __init__(self):
        self.product_name: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    # ─────────────────── HTTP client management ────────────────────

    def _random_headers(self, referer: str = "https://www.flipkart.com") -> Dict[str, str]:
        """Generate realistic browser headers with a random User-Agent."""
        ua = random.choice(_USER_AGENTS)
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": referer,
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
        }

    async def _get_client(self):
        """Lazy init the HTTP client."""
        if self._client is None or getattr(self._client, "is_closed", False):
            # Try to use curl_cffi for advanced TLS impersonation (bypasses most bot checks)
            try:
                from curl_cffi import requests as curl_requests
                self._client = curl_requests.AsyncSession(
                    impersonate="chrome110",
                    timeout=30.0
                )
                self._using_curl_cffi = True
                logger.info("Using curl_cffi for Chrome110 TLS impersonation")
            except ImportError:
                # Fallback to standard httpx
                self._client = httpx.AsyncClient(
                    timeout=httpx.Timeout(30.0, connect=15.0),
                    follow_redirects=True,
                    http2=False,
                    limits=httpx.Limits(max_connections=5),
                )
                self._using_curl_cffi = False
                logger.warning("curl_cffi not installed, falling back to httpx")
        return self._client

    async def _close_client(self):
        """Close the HTTP client."""
        if self._client:
            if getattr(self, "_using_curl_cffi", False):
                # curl_cffi AsyncSession
                self._client.close()
            elif not self._client.is_closed:
                # httpx AsyncClient
                await self._client.aclose()
        self._client = None

    # ─────────────────── URL helpers ───────────────────────────────

    @staticmethod
    def _convert_to_review_url(product_url: str) -> str:
        """Convert a Flipkart product URL to its reviews page URL."""
        if "/product-reviews/" in product_url:
            return product_url
        if "/p/" in product_url:
            return product_url.replace("/p/", "/product-reviews/")
        return product_url

    @staticmethod
    def _build_reviews_url(product_url: str, page: int = 1) -> str:
        """Build the reviews page URL with pagination."""
        base = FlipkartHTTPScraper._convert_to_review_url(product_url)
        parsed = urlparse(base)
        qs = parse_qs(parsed.query)
        clean_params = {}
        if "pid" in qs:
            clean_params["pid"] = qs["pid"][0]
        clean_params["marketplace"] = "FLIPKART"
        clean_params["page"] = str(page)
        clean_query = urlencode(clean_params)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{clean_query}"

    @staticmethod
    def _extract_search_term(product_url: str) -> str:
        """Derive a search term from a Flipkart product URL."""
        parsed = urlparse(product_url)
        path = parsed.path.strip("/")
        if "search" in path:
            qs = parse_qs(parsed.query)
            if "q" in qs:
                return qs["q"][0]
        slug = path.split("/")[0] if "/" in path else path
        term = slug.replace("-", " ").strip()
        tokens = [t for t in term.split() if len(t) > 1]
        return " ".join(tokens)

    @staticmethod
    def _extract_pid_from_url(product_url: str) -> Optional[str]:
        """Extract product ID (pid) from URL query params or path."""
        parsed = urlparse(product_url)
        qs = parse_qs(parsed.query)
        if "pid" in qs:
            return qs["pid"][0]
        # pid is sometimes embedded in the path after /p/ or /product-reviews/
        path = parsed.path
        for marker in ("/p/", "/product-reviews/"):
            if marker in path:
                after = path.split(marker, 1)[1]
                # Remove any trailing path segments
                pid_candidate = after.split("/")[0].split("?")[0]
                if pid_candidate:
                    return pid_candidate
        return None

    # ─────────────────── Strategy 1: Flipkart API ─────────────────

    async def _fetch_reviews_via_api(
        self, product_url: str, page: int = 1
    ) -> Optional[List[Dict]]:
        """
        Try to fetch reviews using Flipkart's internal API endpoints.

        Flipkart's React app makes XHR requests to internal endpoints that
        return review data. These endpoints are less aggressively blocked
        than full page loads.
        """
        pid = self._extract_pid_from_url(product_url)
        if not pid:
            logger.debug("Could not extract pid from URL for API call")
            return None

        client = await self._get_client()

        # Flipkart internal API for reviews
        api_url = f"https://www.flipkart.com/api/3/product/reviews"
        params = {
            "productId": pid,
            "page": str(page),
            "count": "10",
            "marketplace": "FLIPKART",
            "sortOrder": "MOST_RECENT",
        }

        headers = {
            "User-Agent": random.choice(_USER_AGENTS),
            "Accept": "application/json",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": product_url,
            "X-User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) FKUA/website/42/website/Desktop",
            "Origin": "https://www.flipkart.com",
        }

        try:
            resp = await client.get(api_url, params=params, headers=headers)

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    return self._parse_api_response(data)
                except (json.JSONDecodeError, KeyError):
                    logger.debug("API response is not valid JSON")
                    return None
            else:
                logger.debug("API returned status %d", resp.status_code)
                return None

        except Exception as e:
            logger.debug("API fetch failed: %s", e)
            return None

    def _parse_api_response(self, data: dict) -> List[Dict]:
        """Parse reviews from Flipkart's internal API response."""
        reviews = []

        # Flipkart API response structure varies but typically has a RESPONSE key
        # with review data nested inside
        try:
            # Navigate the nested response structure
            response_data = data
            if "RESPONSE" in data:
                response_data = data["RESPONSE"]

            # Try multiple known paths for review data
            review_list = None
            for key_path in [
                ["data", "reviews"],
                ["reviews"],
                ["pageData", "reviews"],
                ["result", "reviews"],
            ]:
                curr = response_data
                for key in key_path:
                    if isinstance(curr, dict) and key in curr:
                        curr = curr[key]
                    else:
                        curr = None
                        break
                if curr and isinstance(curr, list):
                    review_list = curr
                    break

            if not review_list:
                # Try to find reviews in any nested structure
                review_list = self._find_reviews_in_json(data)

            if not review_list:
                return []

            for item in review_list:
                review = self._parse_single_api_review(item)
                if review:
                    reviews.append(review)

        except Exception as e:
            logger.debug("Error parsing API response: %s", e)

        return reviews

    def _find_reviews_in_json(self, obj, depth=0) -> Optional[List]:
        """Recursively search for review-like arrays in nested JSON."""
        if depth > 8:
            return None
        if isinstance(obj, dict):
            # Look for keys that suggest reviews
            for key in ("reviews", "reviewList", "REVIEWS", "review"):
                if key in obj and isinstance(obj[key], list) and len(obj[key]) > 0:
                    # Verify it looks like review data
                    first = obj[key][0]
                    if isinstance(first, dict) and any(
                        k in first for k in ("text", "reviewText", "value", "body", "title")
                    ):
                        return obj[key]
            # Recurse into values
            for v in obj.values():
                result = self._find_reviews_in_json(v, depth + 1)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj[:5]:  # Limit recursion breadth
                result = self._find_reviews_in_json(item, depth + 1)
                if result:
                    return result
        return None

    @staticmethod
    def _parse_single_api_review(item: dict) -> Optional[Dict]:
        """Parse a single review from API JSON format."""
        try:
            # Extract text from various possible keys
            text = ""
            for key in ("text", "reviewText", "value", "body", "review"):
                val = item.get(key)
                if isinstance(val, str) and len(val) > 5:
                    text = val
                    break
                elif isinstance(val, dict):
                    # Nested value like {"value": "review text"}
                    inner = val.get("value") or val.get("text") or ""
                    if len(inner) > 5:
                        text = inner
                        break

            # Also check for title
            title = ""
            for key in ("title", "heading", "reviewTitle"):
                val = item.get(key)
                if isinstance(val, str) and val:
                    title = val
                    break
                elif isinstance(val, dict):
                    inner = val.get("value") or val.get("text") or ""
                    if inner:
                        title = inner
                        break

            if title and text:
                text = f"{title}. {text}"
            elif title and not text:
                text = title

            if not text or len(text.strip()) < 5:
                return None

            # Extract rating
            rating = 0
            for key in ("rating", "overallRating", "stars"):
                val = item.get(key)
                if isinstance(val, dict):
                    val = val.get("value") or val.get("rating")
                if val is not None:
                    try:
                        rating = int(float(str(val)))
                        if 1 <= rating <= 5:
                            break
                        rating = 0
                    except (ValueError, TypeError):
                        pass

            # Extract date
            review_date = datetime.now().date()
            for key in ("created", "date", "createdAt", "reviewDate", "timestamp"):
                val = item.get(key)
                if val:
                    try:
                        if isinstance(val, (int, float)):
                            # Unix timestamp (ms or s)
                            ts = val / 1000 if val > 1e12 else val
                            review_date = datetime.fromtimestamp(ts).date()
                        elif isinstance(val, str):
                            review_date = date_parser.parse(val, fuzzy=True).date()
                        break
                    except (ValueError, OverflowError, OSError):
                        pass

            # Extract reviewer name
            reviewer_name = "Flipkart Customer"
            author = item.get("author") or item.get("reviewer") or item.get("userName")
            if isinstance(author, dict):
                reviewer_name = author.get("name") or author.get("value") or reviewer_name
            elif isinstance(author, str) and author:
                reviewer_name = author

            # Certified/verified
            verified = bool(
                item.get("certifiedBuyer")
                or item.get("verified")
                or item.get("isCertifiedBuyer")
            )

            # Helpful count
            helpful = 0
            for key in ("helpfulCount", "upVote", "upvotes", "likes"):
                val = item.get(key)
                if val is not None:
                    try:
                        helpful = int(val)
                        break
                    except (ValueError, TypeError):
                        pass

            return {
                "text": text.strip(),
                "rating": rating,
                "date": review_date,
                "reviewer_name": reviewer_name,
                "verified": verified,
                "helpful_count": helpful,
            }

        except Exception as e:
            logger.debug("Error parsing single API review: %s", e)
            return None

    # ─────────────────── Strategy 2: HTTP page scraping ───────────

    async def _fetch_page(self, url: str, referer: str = "https://www.flipkart.com") -> Optional[str]:
        """Fetch a page with realistic browser headers."""
        client = await self._get_client()
        headers = self._random_headers(referer)

        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.text
            logger.debug("HTTP %d for %s", resp.status_code, url[:80])
            return None
        except Exception as e:
            logger.debug("HTTP fetch failed: %s", e)
            return None

    async def _establish_session(self):
        """Visit flipkart.com to get session cookies."""
        client = await self._get_client()
        headers = self._random_headers(referer="https://www.google.com")
        try:
            await client.get("https://www.flipkart.com", headers=headers)
            await asyncio.sleep(1)
            logger.info("Session established with Flipkart")
        except Exception as e:
            logger.warning("Failed to establish Flipkart session: %s", e)

    async def _scrape_reviews_http(
        self, product_url: str, page_num: int = 1
    ) -> List[Dict]:
        """Fetch and parse reviews from a review page via HTTP."""
        review_url = self._build_reviews_url(product_url, page_num)
        html = await self._fetch_page(review_url, referer=product_url)

        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Extract product name on first page
        if page_num == 1 and not self.product_name:
            self.product_name = self._extract_product_name(soup)

        reviews = []
        seen_texts = set()

        # Try to extract JSON state first (most reliable for modern Flipkart)
        json_reviews = self._extract_reviews_from_initial_state(html)
        if json_reviews:
            for r in json_reviews:
                if r["text"] not in seen_texts:
                    seen_texts.add(r["text"])
                    reviews.append(r)

        # Fallback to HTML parsing if JSON extraction failed
        if not reviews:
            html_reviews = self._parse_reviews_from_soup(soup)
            for r in html_reviews:
                if r["text"] not in seen_texts:
                    seen_texts.add(r["text"])
                    reviews.append(r)

        return reviews

    def _extract_reviews_from_initial_state(self, html: str) -> List[Dict]:
        """Extract reviews from window.__INITIAL_STATE__ JSON."""
        start = html.find("window.__INITIAL_STATE__ = {")
        if start == -1:
            return []

        end = html.find("</script>", start)
        if end == -1:
            return []

        json_str = html[start + len("window.__INITIAL_STATE__ = "):end].rstrip().rstrip(";")
        
        try:
            data = json.loads(json_str)
            reviews = []
            
            # Recursive search for review objects in the JSON
            def find_reviews(obj):
                if isinstance(obj, dict):
                    if "text" in obj and "title" in obj and "rating" in obj:
                        review = self._parse_single_api_review(obj)
                        if review:
                            reviews.append(review)
                        return
                    for k, v in obj.items():
                        find_reviews(v)
                elif isinstance(obj, list):
                    for item in obj:
                        find_reviews(item)
            
            # Usually found in multiWidgetState.widgetsData.slots
            slots = data.get("multiWidgetState", {}).get("widgetsData", {}).get("slots", [])
            find_reviews(slots)
            
            return reviews
        except Exception as e:
            logger.debug("Error parsing __INITIAL_STATE__: %s", e)
            return []

    # ─────────────────── Review parsing (shared with Playwright) ──

    @staticmethod
    def _extract_product_name(soup: BeautifulSoup) -> Optional[str]:
        """Extract product name from page HTML."""
        class_selectors = ["span.B_NuCI", "h1.yhB1nd", "span.VU-ZEz"]
        generic_selectors = ["h1 span", "h1"]

        for selector in class_selectors + generic_selectors:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if 3 < len(text) < 200:
                    return text

        title_tag = soup.find("title")
        if title_tag:
            text = title_tag.get_text(strip=True)
            text = re.sub(r"\s*Reviews:.*", "", text)
            text = re.sub(r"\s*\|.*", "", text)
            text = re.sub(r"\s*-\s*Flipkart.*", "", text)
            if len(text) > 5:
                return text
        return None

    @staticmethod
    def _parse_reviews_from_soup(soup: BeautifulSoup) -> List[Dict]:
        """
        Extract reviews from parsed HTML.

        Reuses the same parsing logic as the Playwright scraper — looks for
        'Certified Buyer' text nodes and walks up to find review containers.
        """
        reviews: List[Dict] = []
        seen_texts: set = set()

        # ── Method 1: "Certified Buyer" anchor ──
        cb_nodes = soup.find_all(string=lambda t: t and "Certified Buyer" in t)

        for cb in cb_nodes:
            container = FlipkartHTTPScraper._find_review_container(cb)
            if container is None:
                continue
            strings = list(container.stripped_strings)
            review = FlipkartHTTPScraper._parse_review_strings(strings)
            if review and review["text"] not in seen_texts:
                seen_texts.add(review["text"])
                reviews.append(review)

        # ── Method 2: Div-based review blocks (fallback for new layouts) ──
        if not reviews:
            reviews = FlipkartHTTPScraper._parse_reviews_div_fallback(soup, seen_texts)

        return reviews

    @staticmethod
    def _find_review_container(cb_node):
        """Walk up from a 'Certified Buyer' text node to find the review container."""
        parent = cb_node.parent
        for _ in range(20):
            if parent is None:
                return None
            parent = parent.parent
            if parent is None or parent.name != "div":
                continue

            inner_cbs = len(
                parent.find_all(string=lambda t: t and "Certified Buyer" in t)
            )
            if inner_cbs != 1:
                continue

            strings = list(parent.stripped_strings)
            if 5 <= len(strings) <= 12:
                return parent

        return None

    @staticmethod
    def _parse_review_strings(strings: List[str]) -> Optional[Dict]:
        """Parse a review from stripped_strings of a container element."""
        if len(strings) < 3:
            return None

        try:
            rating = 0
            review_text = ""
            reviewer_name = "Flipkart Customer"
            review_date = datetime.now().date()
            verified = False

            first_is_rating = strings[0] in ("1", "2", "3", "4", "5")

            if first_is_rating:
                rating = int(strings[0])
                text_parts = []
                hit_read_full = False
                for s in strings[1:]:
                    if s == "Certified Buyer":
                        break
                    if s == "Read full review":
                        hit_read_full = True
                        continue
                    if hit_read_full:
                        continue
                    if s in ("1", "2", "3", "4", "5"):
                        continue
                    text_parts.append(s)
                review_text = ". ".join(text_parts).strip()
            else:
                review_text = strings[0]

            # Clean truncation markers
            review_text = review_text.strip(".")
            if review_text.startswith("..."):
                review_text = review_text[3:]
            if review_text.endswith("..."):
                review_text = review_text[:-3]
            review_text = review_text.strip()

            if not review_text or len(review_text) < 5:
                return None

            # Metadata extraction
            for i, s in enumerate(strings):
                if s == "Certified Buyer":
                    verified = True
                    if i > 0:
                        candidate = strings[i - 1].strip(", ")
                        if (
                            candidate
                            and not candidate.isdigit()
                            and candidate != "Read full review"
                            and len(candidate) < 60
                            and candidate != review_text
                        ):
                            reviewer_name = candidate

                # Date parsing
                cleaned = s.strip("· ").strip()

                if "ago" in cleaned.lower():
                    match = re.search(
                        r"(\d+)\s*(month|year|day|week|hour)s?\s*ago",
                        cleaned,
                        re.IGNORECASE,
                    )
                    if match:
                        num = int(match.group(1))
                        unit = match.group(2).lower()
                        now = datetime.now()
                        if unit == "year":
                            try:
                                review_date = now.replace(year=now.year - num).date()
                            except ValueError:
                                review_date = (now - timedelta(days=num * 365)).date()
                        elif unit == "month":
                            month = now.month - num
                            year = now.year
                            while month <= 0:
                                month += 12
                                year -= 1
                            try:
                                review_date = now.replace(year=year, month=month).date()
                            except ValueError:
                                review_date = (now - timedelta(days=num * 30)).date()
                        else:
                            days = {"day": 1, "week": 7, "hour": 0}.get(unit, 0)
                            review_date = (now - timedelta(days=num * days)).date()

                elif "," in cleaned and len(cleaned) < 20:
                    months = [
                        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
                    ]
                    if any(m in cleaned for m in months):
                        try:
                            d = date_parser.parse(cleaned, fuzzy=True).date()
                            if d <= datetime.now().date():
                                review_date = d
                        except (ValueError, OverflowError):
                            pass

            return {
                "text": review_text,
                "rating": rating,
                "date": review_date,
                "reviewer_name": reviewer_name,
                "verified": verified,
                "helpful_count": 0,
            }
        except Exception as e:
            logger.debug("Parse error: %s", e)
            return None

    @staticmethod
    def _parse_reviews_div_fallback(soup: BeautifulSoup, seen_texts: set) -> List[Dict]:
        """
        Fallback: extract reviews by looking for rating star elements and
        walking to sibling text containers.
        """
        reviews = []

        # Look for review containers by common Flipkart class patterns
        # Flipkart uses generated class names, but review containers often
        # have a consistent structure:
        #   div > div[star-rating] + div[title] + div[text] + div[metadata]
        rating_divs = soup.find_all(
            "div",
            attrs={"class": True},
            string=lambda t: t and t.strip() in ("1", "2", "3", "4", "5"),
        )

        for rd in rating_divs:
            # Walk up to find a review-sized container
            container = rd.parent
            for _ in range(5):
                if container is None:
                    break
                strings = list(container.stripped_strings)
                # A review container typically has 4-15 text elements
                if 4 <= len(strings) <= 15:
                    review = FlipkartHTTPScraper._parse_review_strings(strings)
                    if review and review["text"] not in seen_texts:
                        seen_texts.add(review["text"])
                        reviews.append(review)
                    break
                container = container.parent

        return reviews

    # ─────────────────── Rating estimation ─────────────────────────

    @staticmethod
    def _estimate_rating_from_text(text: str) -> int:
        """Estimate a star rating (1-5) from review text using keyword heuristics."""
        text_lower = text.lower()

        very_positive = (
            "excellent", "amazing", "awesome", "fantastic", "perfect",
            "outstanding", "superb", "love it", "best", "wonderful",
            "brilliant", "incredible", "flawless", "worth every penny",
            "highly recommend", "must buy", "loved it", "10/10", "5/5",
        )
        positive = (
            "good", "great", "nice", "happy", "satisfied", "decent",
            "smooth", "premium", "impressive", "recommended", "value for money",
            "worth", "pleased", "comfortable", "reliable",
        )
        negative = (
            "bad", "poor", "disappointing", "issue", "problem", "slow",
            "average", "mediocre", "not worth", "overpriced", "overheated",
            "overheat", "lag", "lagging", "regret", "faulty",
        )
        very_negative = (
            "worst", "terrible", "horrible", "waste", "pathetic", "useless",
            "broken", "dead", "defective", "fraud", "scam", "never buy",
            "hated", "rubbish", "trash", "disgusting", "awful",
        )

        score = 0
        for kw in very_positive:
            if kw in text_lower:
                score += 2
        for kw in positive:
            if kw in text_lower:
                score += 1
        for kw in negative:
            if kw in text_lower:
                score -= 1
        for kw in very_negative:
            if kw in text_lower:
                score -= 2

        if score >= 3:
            return 5
        elif score >= 1:
            return 4
        elif score == 0:
            return 3
        elif score >= -2:
            return 2
        else:
            return 1

    # ─────────────────── Main entry point ──────────────────────────

    async def scrape_reviews(
        self,
        product_url: str,
        max_reviews: int = 50,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict]:
        """
        Scrape reviews from a Flipkart product URL.

        Tries strategies in order:
        1. Flipkart internal API
        2. HTTP page scraping with BeautifulSoup

        Args:
            product_url: Flipkart product URL
            max_reviews: Maximum reviews to collect
            progress_callback: Optional (current, total) callback

        Returns:
            List of review dicts
        """
        all_reviews: List[Dict] = []
        seen_texts: set = set()

        logger.info("\n%s", "=" * 60)
        logger.info("Flipkart HTTP Scraper — Starting")
        logger.info("  URL : %s", product_url)
        logger.info("  Max : %d", max_reviews)
        logger.info("%s\n", "=" * 60)

        try:
            # Establish session cookies first
            await self._establish_session()

            # ── Strategy 1: Internal API ──
            logger.info("Trying Strategy 1: Flipkart Internal API...")
            api_success = False

            max_pages = min(max(1, (max_reviews // 10) + 2), 50)
            consecutive_empty = 0

            for page_num in range(1, max_pages + 1):
                if len(all_reviews) >= max_reviews:
                    break
                if consecutive_empty >= 3:
                    break

                api_reviews = await self._fetch_reviews_via_api(product_url, page_num)

                if api_reviews:
                    api_success = True
                    added = 0
                    for r in api_reviews:
                        if len(all_reviews) >= max_reviews:
                            break
                        if r["text"] not in seen_texts:
                            seen_texts.add(r["text"])
                            all_reviews.append(r)
                            added += 1

                    logger.info("API page %d: +%d (total %d)", page_num, added, len(all_reviews))
                    consecutive_empty = 0 if added > 0 else consecutive_empty + 1

                    if progress_callback:
                        progress_callback(len(all_reviews), max_reviews)

                    # Be polite between API requests
                    await asyncio.sleep(random.uniform(1.0, 2.5))
                else:
                    consecutive_empty += 1
                    if page_num == 1:
                        logger.info("API returned no results on page 1 — trying HTTP scraping")
                        break

            # ── Strategy 2: HTTP page scraping (if API didn't work or got partial) ──
            if not api_success or len(all_reviews) < min(10, max_reviews):
                logger.info("Trying Strategy 2: HTTP page scraping...")
                consecutive_empty = 0

                for page_num in range(1, max_pages + 1):
                    if len(all_reviews) >= max_reviews:
                        break
                    if consecutive_empty >= 3:
                        break

                    page_reviews = await self._scrape_reviews_http(product_url, page_num)

                    if page_reviews:
                        added = 0
                        for r in page_reviews:
                            if len(all_reviews) >= max_reviews:
                                break
                            if r["text"] not in seen_texts:
                                seen_texts.add(r["text"])
                                all_reviews.append(r)
                                added += 1

                        logger.info(
                            "HTTP page %d: +%d (total %d)", page_num, added, len(all_reviews)
                        )
                        consecutive_empty = 0 if added > 0 else consecutive_empty + 1

                        if progress_callback:
                            progress_callback(len(all_reviews), max_reviews)
                    else:
                        logger.info("HTTP page %d: 0 reviews", page_num)
                        consecutive_empty += 1

                    # Polite delay between page requests
                    await asyncio.sleep(random.uniform(2.0, 4.0))

        except Exception as e:
            logger.error("HTTP scraper error: %s", e)
            import traceback
            traceback.print_exc()
        finally:
            await self._close_client()

        # Estimate ratings for reviews without individual ratings
        no_rating = [r for r in all_reviews if r["rating"] == 0]
        if no_rating:
            logger.info("Estimating ratings for %d reviews (text-based)", len(no_rating))
            for r in no_rating:
                r["rating"] = self._estimate_rating_from_text(r["text"])

        logger.info("\n%s", "=" * 60)
        logger.info("Done — %d reviews collected", len(all_reviews))
        logger.info("%s\n", "=" * 60)

        return all_reviews

    async def scrape_reviews_with_retry(
        self,
        product_url: str,
        max_reviews: int = 50,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        max_attempts: int = 2,
    ) -> List[Dict]:
        """
        Retry wrapper around scrape_reviews.

        If the first attempt returns 0 reviews, wait and retry with a fresh
        HTTP session.
        """
        for attempt in range(1, max_attempts + 1):
            reviews = await self.scrape_reviews(
                product_url, max_reviews, progress_callback
            )
            if reviews:
                return reviews
            if attempt < max_attempts:
                wait = 5.0 * attempt
                logger.warning(
                    "HTTP scrape attempt %d returned 0 reviews — retrying in %.0fs",
                    attempt,
                    wait,
                )
                await asyncio.sleep(wait)
        return []
