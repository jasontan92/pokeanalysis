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
        """Extract listings from Yahoo Auctions search results page."""
        listings = []
        seen_ids = set()

        try:
            # Yahoo Auctions item links contain /item/ or auction ID patterns
            links = page.query_selector_all('a[href*="/jp/auction/"]')

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue

                    # Extract auction ID from URL (e.g., /item/x1234567890)
                    item_match = re.search(r'/jp/auction/([a-zA-Z0-9]+)', href)
                    if not item_match:
                        continue

                    item_id = f'yahoo-{item_match.group(1)}'
                    if item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)

                    # Parse text content
                    try:
                        text = link.inner_text().strip()
                    except:
                        text = ""

                    lines = [l.strip() for l in text.split('\n') if l.strip()]

                    # Filter out price/bid lines to find title
                    title_lines = [
                        l for l in lines
                        if not re.match(r'^[\d,\.]+円?$', l)
                        and '¥' not in l and '￥' not in l
                        and not l.startswith('現在')
                        and not l.startswith('即決')
                        and not l.startswith('入札')
                        and not l.endswith('件')
                        and not l.endswith('時間')
                        and not l.endswith('日')
                        and not re.match(r'^残り', l)
                    ]
                    title = title_lines[0][:100] if title_lines else item_id

                    # Find price - Yahoo Auctions JP uses yen
                    price = None
                    currency = '¥'
                    for line in lines:
                        # Current price: 現在1,234円 or ¥1,234 or just 1,234円
                        yen_match = re.search(r'(?:現在|即決)?[¥￥]?([\d,]+)円?', line)
                        if yen_match and ('円' in line or '¥' in line or '￥' in line or line.startswith('現在') or line.startswith('即決')):
                            try:
                                price = float(yen_match.group(1).replace(',', ''))
                            except:
                                pass
                            break
                        # Bare number that looks like a price
                        elif re.match(r'^[\d,]+$', line):
                            try:
                                price = float(line.replace(',', ''))
                            except:
                                pass
                            break

                    full_link = href if href.startswith('http') else f"{self.BASE_URL}{href}"

                    listings.append({
                        'listing_id': item_id,
                        'item_id': item_id,
                        'title': title,
                        'price': price,
                        'currency': currency,
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
