"""
SNKRDUNK Marketplace Scraper using Playwright.
Searches for Pokemon cards on snkrdunk.com (Japanese marketplace).
Next.js SPA - requires Playwright for rendering.
"""

import logging
import re
from datetime import datetime
from urllib.parse import quote

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)


class SnkrdunkScraper:
    """Scraper for SNKRDUNK marketplace using Playwright."""

    BASE_URL = "https://snkrdunk.com"

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not installed. SNKRDUNK scraping disabled.")

    def search_listings(self, keyword: str, max_pages: int = 1) -> list[dict]:
        """Search for Pokemon cards on SNKRDUNK.

        Args:
            keyword: Search keyword (Japanese)
            max_pages: Maximum pages to fetch
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available. Skipping SNKRDUNK.")
            return []

        all_listings = []
        encoded = quote(keyword)
        search_url = f"{self.BASE_URL}/search?keywords={encoded}"

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

                logger.info(f"Fetching SNKRDUNK: {keyword}")

                try:
                    page.goto(search_url, timeout=60000)

                    # Wait for page to render (Next.js SPA)
                    for _ in range(6):
                        page.wait_for_timeout(5000)
                        title = page.title().lower()
                        if 'just a moment' not in title and 'checking' not in title:
                            break

                    page.wait_for_timeout(3000)

                    listings = self._extract_listings(page)
                    if listings:
                        all_listings.extend(listings)
                        logger.info(f"Found {len(listings)} SNKRDUNK listings")
                    else:
                        logger.info("No SNKRDUNK listings found")

                except PlaywrightTimeout:
                    logger.warning("Timeout loading SNKRDUNK")
                except Exception as e:
                    error_msg = str(e).encode('ascii', 'replace').decode('ascii')
                    logger.error(f"Error loading SNKRDUNK: {error_msg}")

                browser.close()

        except Exception as e:
            logger.error(f"SNKRDUNK scraper error: {e}")

        return all_listings

    def _extract_listings(self, page) -> list[dict]:
        """Extract listings from SNKRDUNK search results page."""
        listings = []
        seen_ids = set()

        try:
            tiles = page.query_selector_all('a[class*=productTile]')

            for tile in tiles:
                try:
                    href = tile.get_attribute('href') or ''

                    # Extract listing ID from URL
                    # Format: /apparels/{product_id}/used/{listing_id}
                    id_match = re.search(r'/(\d+)/used/(\d+)', href)
                    if not id_match:
                        id_match = re.search(r'/(\d+)', href)
                    if not id_match:
                        continue

                    listing_id = f"snkr-{id_match.group(0).replace('/', '-').strip('-')}"
                    if listing_id in seen_ids:
                        continue
                    seen_ids.add(listing_id)

                    # Get title
                    title_el = tile.query_selector('span[class*=productName]')
                    title = title_el.inner_text().strip()[:120] if title_el else ''
                    if not title:
                        continue

                    # Get price
                    price = None
                    price_el = tile.query_selector('span[class*=productPrice]')
                    if price_el:
                        price_text = price_el.inner_text().strip()
                        price_match = re.search(r'([\d,]+)', price_text)
                        if price_match:
                            try:
                                price = float(price_match.group(1).replace(',', ''))
                            except ValueError:
                                pass

                    # Get condition/grade
                    grade = None
                    grade_el = tile.query_selector('div[class*=conditionLabel]')
                    if grade_el:
                        grade = grade_el.inner_text().strip()

                    # Get image URL
                    image_url = None
                    img_el = tile.query_selector('img')
                    if img_el:
                        image_url = img_el.get_attribute('src') or None

                    full_link = href if href.startswith('http') else f"{self.BASE_URL}{href}"

                    listings.append({
                        'listing_id': listing_id,
                        'item_id': listing_id,
                        'title': f"{grade} {title}" if grade else title,
                        'price': price,
                        'listing_type': 'buy_now',
                        'link': full_link,
                        'image_url': image_url,
                        'platform': 'snkrdunk',
                        'scraped_at': datetime.now().isoformat(),
                    })

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Error extracting SNKRDUNK listings: {e}")

        return listings


if __name__ == '__main__':
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    scraper = SnkrdunkScraper()
    print("Testing SNKRDUNK search...")
    listings = scraper.search_listings('旧裏初版psa')
    print(f"Total listings found: {len(listings)}")
    for listing in listings[:10]:
        title = listing.get('title', '?')[:60]
        price = listing.get('price', '?')
        print(f"  - {title} - ¥{price}")
