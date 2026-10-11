"""
Yahoo Auctions Japan (ヤフオク) Scraper.
Searches for listings on auctions.yahoo.co.jp.

The search results page is server-rendered, so it is fetched with a plain
HTTP request first (~1.3s, vs ~13s for a browser). Playwright is only used
when that reply is inconclusive — e.g. a bot challenge. The browser path
requires xvfb on Linux (headless=False needed to bypass bot detection).
"""

import logging
import re
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class _YahooBrowser:
    """Chromium launched on first use and kept for many searches."""

    def __init__(self):
        self._pw = None
        self._browser = None
        self.page = None

    def get_page(self):
        if self.page is None:
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                ]
            )
            context = self._browser.new_context(
                user_agent=YahooAuctionsScraper.USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
                locale='ja-JP',
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                window.chrome = {runtime: {}};
            """)
            self.page = context.new_page()
        return self.page

    def close(self):
        try:
            if self._browser is not None:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._pw is not None:
                self._pw.stop()
        except Exception:
            pass
        self._pw = self._browser = self.page = None


class YahooAuctionsScraper:
    """Scraper for Yahoo Auctions Japan: plain HTTP first, Playwright fallback."""

    BASE_URL = "https://auctions.yahoo.co.jp"
    USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    # Class on the "no results" heading (条件に一致する商品は見つかりませんでした).
    # Yahoo serves that page with HTTP 404, so the status code alone can't be
    # used to tell "no results" from "failed".
    EMPTY_MARKER = 'Empty__title'
    # Same message as rendered text, for the browser path.
    EMPTY_TEXT = '条件に一致する商品は見つかりませんでした'
    # Upper bound on waiting for results on the browser path.
    RESULTS_TIMEOUT_S = 15
    # After this many inconclusive HTTP replies in a row (e.g. the runner's IP
    # is being challenged), stop trying HTTP for the rest of the run.
    HTTP_GIVE_UP_AFTER = 3

    def __init__(self):
        self.http = requests.Session()
        # Full browser-ish header set: with only User-Agent + Accept-Language,
        # GitHub's runner IPs started getting a page with neither results nor
        # the empty-results marker (logged as "reply inconclusive").
        self.http.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                       'image/avif,image/webp,*/*;q=0.8'),
            'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Cache-Control': 'max-age=0',
        })
        self._http_failures = 0
        self._warmed_up = False
        self._browser = None
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not installed. Yahoo browser fallback disabled.")

    def _search_url(self, keyword: str) -> str:
        encoded = quote(keyword)
        # Sort by newest, 100 per page (max) so matches aren't capped off page 1
        return f"{self.BASE_URL}/search/search?p={encoded}&va={encoded}&exflg=1&b=1&n=100&s1=new&o1=d"

    def search_listings(self, keyword: str, max_pages: int = 1) -> list[dict]:
        """Search for listings on Yahoo Auctions Japan.

        Args:
            keyword: Search keyword (Japanese or English)
            max_pages: Maximum pages to fetch
        """
        if BS4_AVAILABLE and self._http_failures < self.HTTP_GIVE_UP_AFTER:
            self._warm_up()
            listings = self._search_http(keyword)
            if listings is not None:
                self._http_failures = 0
                logger.info(f"Yahoo Auctions via HTTP ({keyword}): {len(listings)} listings")
                return listings
            self._http_failures += 1
            logger.warning(f"Yahoo HTTP reply inconclusive for ({keyword}); using browser "
                           f"({self._http_failures}/{self.HTTP_GIVE_UP_AFTER})")
            if self._http_failures >= self.HTTP_GIVE_UP_AFTER:
                logger.warning("Yahoo HTTP disabled for the rest of this run; browser only.")
        return self._search_browser(keyword)

    def _warm_up(self):
        """Make one throwaway search so Yahoo sets its cookies.

        Without cookies Yahoo treats the request as a first visit and can
        return a broadened "related items" page instead of the exact matches:
        for "ポケットモンスター ゲームボーイ VGA" that was 100 unrelated listings
        rather than the one real VGA-graded copy. The old scraper opened a
        fresh browser for every keyword, so every Yahoo search was a first
        visit. The session keeps the cookies after this, so it runs once.
        """
        if self._warmed_up:
            return
        self._warmed_up = True
        try:
            self.http.get(self._search_url('a'), timeout=20)
        except requests.RequestException as e:
            logger.warning(f"Yahoo warm-up request failed: {e}")

    def _search_http(self, keyword: str) -> Optional[list[dict]]:
        """Fetch the results page without a browser.

        Returns the listings, [] for a genuine "no results" page, or None when
        the reply can't be trusted (challenge page, network error, markup
        change) so the caller falls back to the browser.
        """
        try:
            resp = self.http.get(self._search_url(keyword), timeout=20)
        except requests.RequestException as e:
            logger.warning(f"Yahoo HTTP request failed: {e}")
            return None
        html = resp.text
        listings = self._parse_listings(BeautifulSoup(html, 'lxml').select('a[data-auction-id]'),
                                        lambda a, name: a.get(name))
        if listings:
            return listings
        if self.EMPTY_MARKER in html:
            return []
        # Say why it was rejected, so a blocked runner can be told apart from
        # a markup change without having to reproduce it.
        soup_title = ''
        try:
            t = BeautifulSoup(html, 'lxml').title
            soup_title = (t.string or '').strip()[:80] if t else ''
        except Exception:
            pass
        logger.warning(f"Yahoo HTTP unusable: status={resp.status_code} "
                       f"bytes={len(html)} title={soup_title!r} "
                       f"anchors={html.count('data-auction-id')}")
        return None

    @contextmanager
    def browser_session(self):
        """Reuse one browser for every fallback search in this block.

        Without it each fallback launched its own Chromium (~13s/keyword, and
        a cookie-less context that gets Yahoo's broadened "related items"
        results). The browser is created on first use, so a run where HTTP
        works never launches one. Single-threaded: Playwright's sync API binds
        objects to the creating thread.
        """
        self._browser = _YahooBrowser()
        try:
            yield
        finally:
            self._browser.close()
            self._browser = None

    def _search_session(self, keyword: str) -> Optional[list[dict]]:
        """Fallback search on the shared browser. None if it isn't usable."""
        if self._browser is None or not PLAYWRIGHT_AVAILABLE:
            return None
        try:
            page = self._browser.get_page()
            page.goto(self._search_url(keyword), timeout=30000,
                      wait_until='domcontentloaded')
            state = self._wait_for_results(page)
            if state == 'empty':
                logger.info(f"Yahoo Auctions via browser ({keyword}): 0 listings")
                return []
            if state == 'unknown':
                # Neither results nor the empty heading: don't report an empty
                # result from a page we don't understand. Returning None makes
                # the caller retry on a fresh one-off browser (the old path),
                # so a broken shared session costs speed, never listings.
                logger.warning(f"Yahoo shared browser saw no results and no empty "
                               f"marker ({keyword}); retrying with a fresh browser")
                return None
            listings = self._extract_listings(page)
            logger.info(f"Yahoo Auctions via browser ({keyword}): {len(listings)} listings")
            return listings
        except Exception as e:
            err = str(e).encode('ascii', 'replace').decode('ascii')
            logger.warning(f"Yahoo shared-browser search failed ({err}); "
                           f"relaunching for the next keyword")
            self._browser.close()
            return None

    def _wait_for_results(self, page) -> str:
        """Wait for result anchors or the empty-results heading.

        Replaces a fixed 5s + 3s sleep. Yahoo is server-rendered, so results
        are usually there as soon as navigation finishes.
        """
        deadline = time.monotonic() + self.RESULTS_TIMEOUT_S
        while time.monotonic() < deadline:
            title = (page.title() or '').lower()
            if 'just a moment' in title or 'checking' in title or 'verify' in title:
                deadline = max(deadline, time.monotonic() + 5)
            elif page.query_selector('a[data-auction-id]'):
                return 'items'
            elif page.get_by_text(self.EMPTY_TEXT).count():
                return 'empty'
            time.sleep(0.25)
        return 'unknown'

    def _search_browser(self, keyword: str) -> list[dict]:
        """Playwright path, used only when HTTP is inconclusive."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available. Skipping Yahoo Auctions.")
            return []

        shared = self._search_session(keyword)
        if shared is not None:
            return shared

        all_listings = []
        search_url = self._search_url(keyword)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                    ]
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='ja-JP',
                )

                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                    window.chrome = {runtime: {}};
                """)

                page = context.new_page()
                logger.info(f"Fetching Yahoo Auctions ({keyword})...")

                try:
                    page.goto(search_url, timeout=60000)

                    # Wait for any challenge/redirect
                    for _ in range(6):
                        page.wait_for_timeout(5000)
                        title = page.title().lower()
                        if 'just a moment' not in title and 'checking' not in title:
                            break

                    page.wait_for_timeout(3000)

                    listings = self._extract_listings(page)
                    if listings:
                        all_listings.extend(listings)
                        logger.info(f"Found {len(listings)} Yahoo Auctions listings")
                    else:
                        logger.info("No Yahoo Auctions listings found")

                except PlaywrightTimeout:
                    logger.warning("Timeout loading Yahoo Auctions")
                except Exception as e:
                    error_msg = str(e).encode('ascii', 'replace').decode('ascii')
                    logger.error(f"Error loading Yahoo Auctions: {error_msg}")

                browser.close()

        except Exception as e:
            logger.error(f"Yahoo Auctions scraper error: {e}")

        return all_listings

    def _extract_listings(self, page) -> list[dict]:
        """Extract listings from a Playwright page."""
        try:
            links = page.query_selector_all('a[data-auction-id]')
        except Exception as e:
            logger.error(f"Error extracting Yahoo Auctions listings: {e}")
            return []
        return self._parse_listings(links, lambda a, name: a.get_attribute(name))

    def _parse_listings(self, anchors, attr) -> list[dict]:
        """Build listings from result anchors.

        Uses the data-attributes on Product__imageLink anchors, which are the
        same in the server HTML and the rendered page. `attr(anchor, name)`
        reads an attribute from either a BeautifulSoup tag or a Playwright
        element handle.
        """
        listings = []
        seen_ids = set()

        for link in anchors:
            try:
                item_id = attr(link, 'data-auction-id')
                if not item_id or item_id in seen_ids:
                    continue
                seen_ids.add(item_id)

                title = attr(link, 'data-auction-title') or item_id
                title = title[:100]

                price = None
                price_str = attr(link, 'data-auction-price')
                if price_str:
                    try:
                        price = float(price_str.replace(',', ''))
                    except ValueError:
                        pass

                href = attr(link, 'href') or ''
                full_link = href if href.startswith('http') else f"{self.BASE_URL}/jp/auction/{item_id}"

                listings.append({
                    'listing_id': f'yahoo-{item_id}',
                    'item_id': f'yahoo-{item_id}',
                    'title': title,
                    'price': price,
                    'currency': '¥',
                    'listing_type': 'auction',
                    'link': full_link,
                    'platform': 'yahoo_auctions_jp',
                    'scraped_at': datetime.now().isoformat()
                })

            except Exception:
                continue

        return listings


if __name__ == '__main__':
    scraper = YahooAuctionsScraper()
    print("Testing Yahoo Auctions Japan search...")
    listings = scraper.search_listings(keyword='週刊少年ジャンプ 1996年42号')
    print(f"Total listings found: {len(listings)}")
    for listing in listings[:5]:
        title = listing.get('title', '?')[:40]
        price = listing.get('price', '?')
        print(f"  - {title} - ¥{price}")
