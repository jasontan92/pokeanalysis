"""
Yahoo Auctions Japan (ヤフオク) Scraper using Playwright.
Searches for listings on auctions.yahoo.co.jp.
Note: Requires xvfb on Linux (headless=False needed to bypass bot detection).
"""

import logging
import re
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class YahooAuctionsScraper:
    """Scraper for Yahoo Auctions Japan using Playwright."""

    BASE_URL = "https://auctions.yahoo.co.jp"

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not installed. Yahoo Auctions scraping disabled.")

    def search_listings(self, keyword: str, max_pages: int = 1) -> list[dict]:
        """Search for listings on Yahoo Auctions Japan.

        Args:
            keyword: Search keyword (Japanese or English)
            max_pages: Maximum pages to fetch
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available. Skipping Yahoo Auctions.")
            return []

        all_listings = []
        encoded = quote(keyword)
        # Sort by newest, 50 per page
        search_url = f"{self.BASE_URL}/search/search?p={encoded}&va={encoded}&exflg=1&b=1&n=50&s1=new&o1=d"

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
        """Extract listings from Yahoo Auctions search results page.

        Uses data-attributes on Product__imageLink anchors for reliable extraction.
        """
        listings = []
        seen_ids = set()

        try:
            links = page.query_selector_all('a[data-auction-id]')

            for link in links:
                try:
                    item_id = link.get_attribute('data-auction-id')
                    if not item_id or item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)

                    title = link.get_attribute('data-auction-title') or item_id
                    title = title[:100]

                    price = None
                    price_str = link.get_attribute('data-auction-price')
                    if price_str:
                        try:
                            price = float(price_str.replace(',', ''))
                        except ValueError:
                            pass

                    href = link.get_attribute('href') or ''
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

        except Exception as e:
            logger.error(f"Error extracting Yahoo Auctions listings: {e}")

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
