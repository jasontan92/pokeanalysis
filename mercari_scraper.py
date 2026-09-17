"""
Mercari Japan Marketplace Scraper using Playwright.
Searches for 旧裏初版 (no rarity/first edition) Pokemon cards.
Note: Requires xvfb on Linux (headless=False needed to bypass bot detection).
"""

import logging
import re
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


ITEM_SELECTOR = 'a[href*="/item/"]'
# Mercari's empty-results message.
EMPTY_TEXT = '出品された商品がありません'


class MercariSession:
    """One browser kept open across many searches.

    Launching Chromium per keyword cost ~2-3s each, and the old fixed
    5s + 3s sleep ran even when results had already rendered. A session
    reuses the browser and waits only as long as the page actually needs.
    Must be created and used on a single thread (Playwright sync API).
    """

    # Upper bound on waiting for results OR the empty message. Deliberately
    # longer than the ~8s the old fixed sleep allowed, so a slow render is
    # waited out rather than silently read as "no results".
    RESULTS_TIMEOUT_S = 15
    # After the first tile appears, wait until the tile count stops changing.
    SETTLE_QUIET_S = 1.5
    SETTLE_MAX_S = 5
    # Then wait until every tile shows its text (title + price).
    RENDER_MAX_S = 4
    POLL_S = 0.25

    def __init__(self, playwright):
        self.browser = playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                # Keep timers/rendering at full speed even when the window
                # is hidden behind others (matters when run on a desktop).
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
            ]
        )
        context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='ja-JP',
        )
        # Stealth scripts
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = {runtime: {}};
        """)
        self.page = context.new_page()

    def close(self):
        try:
            self.browser.close()
        except Exception:
            pass

    def search(self, keyword: Optional[str] = None, url: Optional[str] = None,
               attempts: int = 2) -> list[dict]:
        """Run one search and return its listings.

        A page that shows neither tiles nor the empty message within
        RESULTS_TIMEOUT_S is retried once — on CI Mercari occasionally
        renders nothing (slow render or soft bot gating).
        """
        search_url = url or (f"{MercariScraper.BASE_URL}/search?keyword={quote(keyword)}"
                             f"&order=desc&sort=created_time&status=on_sale")
        label = f' ({keyword})' if keyword else ''
        for attempt in range(1, attempts + 1):
            logger.info(f"Fetching Mercari Japan{label}...")
            state = self._load(search_url)
            if state == 'items':
                listings = MercariScraper._extract_listings(self.page)
                logger.info(f"Found {len(listings)} Mercari Japan listings")
                return listings
            if state == 'empty':
                logger.info("No Mercari Japan listings found")
                return []
            logger.warning(f"Mercari showed no results or empty message{label} "
                           f"(attempt {attempt}/{attempts})")
            if attempt < attempts:
                time.sleep(3)
        return []

    def _load(self, url: str) -> str:
        """Navigate and wait. Returns 'items', 'empty' or 'unknown'."""
        page = self.page
        try:
            page.goto(url, timeout=30000, wait_until='domcontentloaded')
        except PlaywrightTimeout:
            logger.warning("Timeout loading Mercari Japan")
            return 'unknown'

        state = 'unknown'
        deadline = time.monotonic() + self.RESULTS_TIMEOUT_S
        while time.monotonic() < deadline:
            title = (page.title() or '').lower()
            if 'just a moment' in title or 'checking' in title:
                # Bot challenge: give it the time it needs.
                deadline = max(deadline, time.monotonic() + 5)
            elif page.query_selector(ITEM_SELECTOR):
                state = 'items'
                break
            elif page.get_by_text(EMPTY_TEXT).count():
                state = 'empty'
                break
            time.sleep(self.POLL_S)

        if state != 'items':
            return state

        # Tiles can arrive in batches: wait for the count to stop changing.
        count, stable_since = -1, time.monotonic()
        settle_deadline = time.monotonic() + self.SETTLE_MAX_S
        while time.monotonic() < settle_deadline:
            n = len(page.query_selector_all(ITEM_SELECTOR))
            if n != count:
                count, stable_since = n, time.monotonic()
            elif time.monotonic() - stable_since >= self.SETTLE_QUIET_S:
                break
            time.sleep(self.POLL_S)

        # And for each tile's text (title + price) to render. Tiles that are
        # still blank after this are skipped by _extract_listings.
        render_deadline = time.monotonic() + self.RENDER_MAX_S
        while time.monotonic() < render_deadline:
            if page.evaluate(
                """(sel) => [...document.querySelectorAll(sel)]
                     .every(a => /[¥￥$]/.test(a.innerText))""",
                ITEM_SELECTOR,
            ):
                break
            time.sleep(self.POLL_S)
        return 'items'


class MercariScraper:
    """Scraper for Mercari Japan marketplace using Playwright."""

    BASE_URL = "https://jp.mercari.com"
    # Direct search URL for 旧裏初版psa (no rarity PSA cards), sorted by newest, on sale only
    SEARCH_URL = "https://jp.mercari.com/search?keyword=%E6%97%A7%E8%A3%8F%E5%88%9D%E7%89%88psa&order=desc&sort=created_time&status=on_sale"

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not installed. Mercari scraping disabled.")

    @contextmanager
    def session(self):
        """Yield a MercariSession that reuses one browser for many searches."""
        with sync_playwright() as p:
            s = MercariSession(p)
            try:
                yield s
            finally:
                s.close()

    def search_listings(self, max_pages: int = 1, keyword: str = None) -> list[dict]:
        """Search for Pokemon cards on Mercari Japan (one-off, own browser).

        Args:
            max_pages: Maximum pages to fetch
            keyword: Custom search keyword. If None, uses the default NR search URL.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available. Skipping Mercari.")
            return []
        try:
            with self.session() as s:
                return s.search(keyword=keyword, url=None if keyword else self.SEARCH_URL)
        except Exception as e:
            print(f"Mercari scraper error: {e}")
            return []

    @staticmethod
    def _extract_listings(page) -> list[dict]:
        """Extract listings from Mercari Japan search results page."""
        listings = []
        seen_ids = set()

        try:
            # Find all item links
            links = page.query_selector_all(ITEM_SELECTOR)

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue

                    item_match = re.search(r'/item/([a-zA-Z0-9]+)', href)
                    if not item_match:
                        continue

                    item_id = f'mercari-{item_match.group(1)}'
                    if item_id in seen_ids:
                        continue

                    # Parse text content - handle encoding issues
                    try:
                        text = link.inner_text().strip()
                    except:
                        text = ""

                    # A tile that hasn't rendered yet has no text. Skip it
                    # rather than return it untitled: the monitor marks
                    # listings that fail validation as seen, so an untitled
                    # tile would never be alerted on. Skipped, it's retried
                    # on the next run.
                    if not text:
                        continue
                    seen_ids.add(item_id)

                    lines = [l.strip() for l in text.split('\n') if l.strip()]

                    # Filter out price lines (SG$, US$, yen, numbers, etc.) to find the actual title
                    title_lines = [
                        l for l in lines
                        if not l.startswith('SG')
                        and not l.startswith('US$')
                        and not l.startswith('$')
                        and not l.startswith('¥')
                        and not l.startswith('￥')
                        and '¥' not in l and '￥' not in l
                        and not l.startswith('現在')
                        and not re.match(r'^[\d,\.]+$', l.replace(',', ''))
                    ]
                    if not title_lines:
                        continue
                    title = ' '.join(title_lines)[:100]

                    # Find price and detect currency from page text
                    price = None
                    currency = '$'
                    for line in lines:
                        if '¥' in line or '￥' in line:
                            yen_match = re.search(r'[¥￥]([\d,]+)', line)
                            if yen_match:
                                try:
                                    price = float(yen_match.group(1).replace(',', ''))
                                    currency = '¥'
                                except:
                                    pass
                                break
                        elif line.startswith('US$') or line.startswith('SG$') or line.startswith('$') or (line and line[0].isdigit()):
                            price_match = re.search(r'(?:US\$|SG\$|\$)?([\d,]+(?:\.\d{2})?)', line)
                            if price_match:
                                try:
                                    price = float(price_match.group(1).replace(',', ''))
                                    currency = '$'
                                except:
                                    pass
                                break

                    full_link = href if href.startswith('http') else f"{MercariScraper.BASE_URL}{href}"

                    listings.append({
                        'listing_id': item_id,
                        'item_id': item_id,
                        'title': title,
                        'price': price,
                        'currency': currency,
                        'listing_type': 'buy_now',
                        'link': full_link,
                        'platform': 'mercari_jp',
                        'scraped_at': datetime.now().isoformat()
                    })

                except Exception:
                    continue

        except Exception as e:
            print(f"Error extracting Mercari listings: {e}")

        return listings


if __name__ == '__main__':
    scraper = MercariScraper()
    print("Testing Mercari Japan search...")
    listings = scraper.search_listings(max_pages=1)
    print(f"Total listings found: {len(listings)}")
    for listing in listings[:5]:
        title = listing.get('title', '?')[:40]
        price = listing.get('price', '?')
        print(f"  - {title} - {price} yen")
