"""Flipkart product review scraper using Playwright browser automation."""
import asyncio
import functools
import logging
import re
from datetime import datetime
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from dateutil import parser as date_parser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _retry_async(max_retries: int = 2, backoff: float = 2.0, exceptions=(Exception,)):
    """Decorator that retries an async function with exponential backoff."""
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 2):  # +1 for initial try
                try:
                    return await fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt <= max_retries:
                        wait = backoff * attempt
                        logger.warning(
                            "%s attempt %d/%d failed: %s — retrying in %.1fs",
                            fn.__name__, attempt, max_retries + 1, exc, wait,
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            fn.__name__, max_retries + 1, exc,
                        )
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


class FlipkartScraper:
    """
    Scraper for Flipkart product reviews using Playwright.

    Flipkart blocks all direct HTTP requests with reCAPTCHA, so we use
    headless Chromium via Playwright.  Even with a real browser, direct
    navigation to product / review URLs returns "Something went wrong".

    Working flow:
      1.  Visit flipkart.com  (establishes session cookies)
      2.  Search for the product using the search bar
      3.  Click the product link  (opens in a new tab)
      4.  Navigate from the product page to the reviews page
      5.  Paginate through reviews
    """

    def __init__(self):
        self.product_name: Optional[str] = None
        self._browser = None
        self._context = None
        self._pw = None

    # ───────────────────────── URL helpers ──────────────────────────

    @staticmethod
    def _extract_search_term(product_url: str) -> str:
        """
        Derive a search term from a Flipkart product URL.

        Example:
            .../apple-iphone-15-black-128-gb/p/itm…  →  "apple iphone 15 black 128 gb"
        """
        parsed = urlparse(product_url)
        path = parsed.path.strip("/")

        # Already a search URL → use the q parameter
        if "search" in path:
            qs = parse_qs(parsed.query)
            if "q" in qs:
                return qs["q"][0]

        # Product URL → first path segment is the slug
        slug = path.split("/")[0] if "/" in path else path
        term = slug.replace("-", " ").strip()
        tokens = [t for t in term.split() if len(t) > 1]
        return " ".join(tokens)

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
        base = FlipkartScraper._convert_to_review_url(product_url)
        # Parse and keep only essential query params
        parsed = urlparse(base)
        qs = parse_qs(parsed.query)
        clean_params = {}
        if "pid" in qs:
            clean_params["pid"] = qs["pid"][0]
        clean_params["marketplace"] = "FLIPKART"
        clean_params["page"] = str(page)
        from urllib.parse import urlencode
        clean_query = urlencode(clean_params)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{clean_query}"
        return clean_url

    # ───────────────────── Browser management ──────────────────────

    async def _launch_browser(self):
        """Launch Playwright Chromium browser."""
        from playwright.async_api import async_playwright
        import sys

        try:
            self._pw = await async_playwright().start()
        except NotImplementedError:
            # Windows fallback: the current event loop doesn't support
            # subprocesses (SelectorEventLoop). Switch to ProactorEventLoop
            # for this thread and retry.
            if sys.platform == "win32":
                import asyncio
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                loop = asyncio.ProactorEventLoop()
                asyncio.set_event_loop(loop)
                self._pw = await async_playwright().start()
            else:
                raise
        self._browser = await self._pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-IN",
        )
        # Stealth: hide webdriver flag
        await self._context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            """
        )

    async def _close_browser(self):
        """Release browser resources."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._pw:
                await self._pw.stop()
        except Exception:
            pass
        finally:
            self._context = self._browser = self._pw = None

    # ───────────────────── Navigation flow ─────────────────────────

    @_retry_async(max_retries=2, backoff=3.0)
    async def _navigate_via_search(self, search_term: str, page):
        """Search for a product on Flipkart. Returns the search-results page."""
        logger.info("Visiting flipkart.com ...")
        last_nav_error = None
        for wait_until in ("domcontentloaded", "load"):
            try:
                await page.goto(
                    "https://www.flipkart.com",
                    wait_until=wait_until,
                    timeout=60_000,
                )
                last_nav_error = None
                break
            except Exception as exc:
                last_nav_error = exc
                logger.warning(
                    "Flipkart landing failed with wait_until=%s: %s",
                    wait_until,
                    exc,
                )

        if last_nav_error is not None:
            raise last_nav_error

        await page.wait_for_timeout(2000)

        # Dismiss login pop-up
        try:
            close_btn = page.locator(
                "button:has-text('✕'), span:has-text('✕'), button:has-text('×')"
            )
            if await close_btn.count() > 0:
                await close_btn.first.click()
                await page.wait_for_timeout(500)
        except Exception:
            pass

        # Type and search – Flipkart has two input[name='q'], one is readonly
        logger.info("Searching: %s", search_term)
        search_input = page.locator("input[name='q']:not([readonly])")
        if await search_input.count() == 0:
            search_input = page.locator("input[type='text']:not([readonly])").first

        await search_input.fill(search_term)
        await page.wait_for_timeout(500)
        await search_input.press("Enter")
        await page.wait_for_timeout(3000)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(2000)

        return page

    async def _find_product_and_navigate(self, search_page):
        """
        Click the first product on the search results page.
        Returns (product_page, product_url, review_base_url) or (None, None, None).
        """
        product_links = search_page.locator("a[href*='/p/']")
        count = await product_links.count()

        if count == 0:
            logger.warning("No product links found on search page")
            return None, None, None

        logger.info("Found %d product links – clicking first ...", count)

        async with self._context.expect_page(timeout=15_000) as new_page_info:
            await product_links.first.click()

        product_page = await new_page_info.value
        await product_page.wait_for_load_state("domcontentloaded")
        await product_page.wait_for_timeout(3000)

        product_url = product_page.url
        logger.info("Product page: %s", product_url)

        # Extract product name
        html = await product_page.content()
        soup = BeautifulSoup(html, "html.parser")
        self.product_name = self._extract_product_name_from_soup(soup)
        if self.product_name:
            logger.info("Product: %s", self.product_name)

        # Extract a review page base URL from product page links
        review_base_url = None
        review_links = soup.find_all("a", href=lambda h: h and "product-reviews" in h)
        if review_links:
            href = review_links[0].get("href", "")
            if href.startswith("/"):
                href = f"https://www.flipkart.com{href}"
            # Strip page param if present, we'll add our own
            href = re.sub(r"[&?]page=\d+", "", href)
            review_base_url = href
            logger.info("Found review base URL from product page")

        return product_page, product_url, review_base_url

    @_retry_async(max_retries=1, backoff=2.0)
    async def _open_product_direct(self, page, product_url: str):
        """Open the provided product URL directly and extract review link hints."""
        logger.info("Opening product URL directly ...")
        await page.goto(
            product_url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        await page.wait_for_timeout(3000)

        resolved_url = page.url
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        if not self.product_name:
            self.product_name = self._extract_product_name_from_soup(soup)

        review_base_url = None
        review_links = soup.find_all("a", href=lambda h: h and "product-reviews" in h)
        if review_links:
            href = review_links[0].get("href", "")
            if href.startswith("/"):
                href = f"https://www.flipkart.com{href}"
            href = re.sub(r"[&?]page=\d+", "", href)
            review_base_url = href

        if not review_base_url and "/p/" in resolved_url:
            review_base_url = self._convert_to_review_url(resolved_url)

        return page, resolved_url, review_base_url

    @_retry_async(max_retries=1, backoff=2.0)
    async def _navigate_to_reviews(
        self, product_page, product_url: str, page_num: int = 1,
        review_base_url: Optional[str] = None,
    ):
        """
        Navigate to a review page and return its BeautifulSoup, or None.
        
        Uses JavaScript navigation (window.location.href) instead of
        Playwright's goto() because Flipkart's React SPA renders review
        content only when navigated from within the existing page context.
        """
        # Build review URL – prefer the actual link from product page
        if review_base_url:
            sep = "&" if "?" in review_base_url else "?"
            review_url = f"{review_base_url}{sep}page={page_num}"
        else:
            review_url = self._build_reviews_url(product_url, page_num)
        
        logger.info("Reviews page %d", page_num)

        try:
            # JavaScript navigation preserves SPA context
            await product_page.evaluate(f"window.location.href = '{review_url}'")
            await product_page.wait_for_timeout(6000)

            # Scroll to trigger lazy-loading
            await product_page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight / 2)"
            )
            await product_page.wait_for_timeout(2000)
            await product_page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )
            await product_page.wait_for_timeout(2000)

            html = await product_page.content()
            return BeautifulSoup(html, "html.parser")
        except Exception as e:
            logger.warning("Error on reviews page: %s", e)
            return None

    # ──────────────────── Review parsing ───────────────────────────

    @staticmethod
    def _extract_product_name_from_soup(soup: BeautifulSoup) -> Optional[str]:
        """Extract product name from page HTML (multiple selectors + fallbacks)."""
        # Specific class selectors (may break when Flipkart updates CSS)
        class_selectors = ["span.B_NuCI", "h1.yhB1nd", "span.VU-ZEz"]
        # Generic fallback selectors (layout-based, more stable)
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
        Extract individual reviews from a parsed Flipkart page.

        Two known layouts:

        A) Review page  (/product-reviews/)
           Container: [review_text, name, location, "Certified Buyer", date]
           – review_text may have "…" prefix/suffix
           – No individual star rating

        B) Search results  (search?q=…)
           Container: [rating, title, text, "Read full review", name, "Certified Buyer", date]
           – rating is "1".."5"
        """
        reviews: List[Dict] = []
        seen_texts: set = set()

        cb_nodes = soup.find_all(string=lambda t: t and "Certified Buyer" in t)

        for cb in cb_nodes:
            container = FlipkartScraper._find_review_container(cb)
            if container is None:
                continue

            strings = list(container.stripped_strings)
            review = FlipkartScraper._parse_review_strings(strings)
            if review and review["text"] not in seen_texts:
                seen_texts.add(review["text"])
                reviews.append(review)

        return reviews

    @staticmethod
    def _find_review_container(cb_node):
        """
        Walk up from a "Certified Buyer" text node to find the review container.
        
        Return the FIRST div with exactly 1 inner CB and >= 5 stripped_strings.
        This avoids picking up metadata-only wrappers (name + CB + date = 3-4 strings)
        while stopping before section-level wrappers that add header text.
        """
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
            # A real review container has at least 5 strings:
            #   Search: [rating, title, text, "Read full review", name, "CB", date] = 7
            #   Review page: [text, name, location, "CB", date] = 5
            if 5 <= len(strings) <= 12:
                return parent

        return None

    @staticmethod
    def _parse_review_strings(strings: List[str]) -> Optional[Dict]:
        """Parse a review from the stripped_strings of a review container."""
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
                # ── Search / old format: [rating, title, text, "Read full review", name, "CB", date] ──
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
                        # Everything after "Read full review" is metadata (name)
                        continue
                    if s in ("1", "2", "3", "4", "5"):
                        continue
                    text_parts.append(s)
                review_text = ". ".join(text_parts).strip()
            else:
                # ── Review-page format: [text, name, loc, CB, date] ──
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

                # Date: "· Apr, 2024" or "Apr, 2024" or "10 months ago"
                cleaned = s.strip("· ").strip()

                # Handle relative dates like "10 months ago", "1 year ago"
                if "ago" in cleaned.lower():
                    from datetime import timedelta
                    import re as _re
                    match = _re.search(r"(\d+)\s*(month|year|day|week|hour)s?\s*ago", cleaned, _re.IGNORECASE)
                    if match:
                        num = int(match.group(1))
                        unit = match.group(2).lower()
                        now = datetime.now()
                        if unit == "year":
                            # Subtract years properly
                            try:
                                review_date = now.replace(year=now.year - num).date()
                            except ValueError:
                                review_date = (now - timedelta(days=num * 365)).date()
                        elif unit == "month":
                            # Subtract months properly
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

    # ───────────────────── Main entry point ────────────────────────

    @staticmethod
    def _estimate_rating_from_text(text: str) -> int:
        """
        Estimate a star rating (1-5) from review text using keyword heuristics.

        Used for review-page reviews where Flipkart does not show individual
        star ratings in the DOM.
        """
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

    async def scrape_reviews(
        self,
        product_url: str,
        max_reviews: int = 50,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict]:
        """
        Scrape reviews from a Flipkart product.

        Args:
            product_url:  Flipkart product URL
            max_reviews:  Maximum number of reviews to collect
            progress_callback:  Optional (current, total) callback

        Returns:
            List of review dicts with keys:
            text, rating, date, reviewer_name, verified, helpful_count
        """
        all_reviews: List[Dict] = []

        logger.info("\n%s", "=" * 60)
        logger.info("Flipkart Scraper — Starting")
        logger.info("  URL : %s", product_url)
        logger.info("  Max : %d", max_reviews)
        logger.info("%s\n", "=" * 60)

        try:
            await self._launch_browser()
            page = await self._context.new_page()

            product_page = None
            product_url_resolved = None
            review_base_url = None

            # ── 1. Try direct product URL first ──
            try:
                product_page, product_url_resolved, review_base_url = await self._open_product_direct(
                    page, product_url
                )
                logger.info("Direct product open succeeded")
            except Exception as direct_err:
                logger.warning("Direct product open failed: %s", direct_err)

            # ── 2. Fallback: search flow if direct open did not yield a product URL ──
            if not product_page or not product_url_resolved:
                search_term = self._extract_search_term(product_url)
                search_page = await self._navigate_via_search(search_term, page)

                # Collect any reviews visible on search result cards
                search_html = await search_page.content()
                search_soup = BeautifulSoup(search_html, "html.parser")
                search_reviews = self._parse_reviews_from_soup(search_soup)

                if search_reviews:
                    for r in search_reviews:
                        if len(all_reviews) >= max_reviews:
                            break
                        if not any(e["text"] == r["text"] for e in all_reviews):
                            all_reviews.append(r)
                    logger.info("Search page: %d reviews", len(all_reviews))

                if progress_callback:
                    progress_callback(len(all_reviews), max_reviews)

                product_page, product_url_resolved, review_base_url = (
                    await self._find_product_and_navigate(search_page)
                )

            if not product_page or not product_url_resolved:
                logger.info("Could not open product page — returning collected reviews only")
                return all_reviews

            # ── 4. Paginate through review pages ──
            consecutive_empty = 0
            max_pages = min(max(1, (max_reviews // 10) + 2), 50)

            for page_num in range(1, max_pages + 1):
                if len(all_reviews) >= max_reviews:
                    logger.info("Reached target (%d)", max_reviews)
                    break
                if consecutive_empty >= 3:
                    logger.info("3 consecutive empty pages — stopping")
                    break

                soup = await self._navigate_to_reviews(
                    product_page,
                    product_url_resolved,
                    page_num,
                    review_base_url=review_base_url,
                )
                if soup is None:
                    consecutive_empty += 1
                    continue

                if page_num == 1 and not self.product_name:
                    self.product_name = self._extract_product_name_from_soup(soup)

                page_reviews = self._parse_reviews_from_soup(soup)

                if not page_reviews:
                    logger.info("Page %d: 0 reviews", page_num)
                    consecutive_empty += 1
                    continue

                added = 0
                for r in page_reviews:
                    if len(all_reviews) >= max_reviews:
                        break
                    if not any(e["text"] == r["text"] for e in all_reviews):
                        all_reviews.append(r)
                        added += 1

                logger.info("Page %d: +%d  (total %d)", page_num, added, len(all_reviews))
                consecutive_empty = 0 if added > 0 else consecutive_empty + 1

                if progress_callback:
                    progress_callback(len(all_reviews), max_reviews)

                await asyncio.sleep(1.5)

        except Exception as e:
            logger.error("Scraper error: %s", e)
            import traceback
            traceback.print_exc()
        finally:
            await self._close_browser()

        # Reviews without individual rating → estimate from text sentiment
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

        If the first attempt returns 0 reviews (e.g. Flipkart served a
        CAPTCHA page), wait and retry with a fresh browser session.
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
                    "Scrape attempt %d returned 0 reviews — retrying in %.0fs",
                    attempt, wait,
                )
                await asyncio.sleep(wait)
        return []
