"""
Mercari Japan Marketplace Scraper using Playwright.
Searches for 旧裏初版 (no rarity/first edition) Pokemon cards.
Note: Requires xvfb on Linux (headless=False needed to bypass bot detection).
"""

import re
from datetime import datetime
from typing import Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class MercariScraper:
    """Scraper for Mercari Japan marketplace using Playwright."""

    BASE_URL = "https://jp.mercari.com"
    # Direct search URL for 旧裏初版psa (no rarity PSA cards), sorted by newest, on sale only
    SEARCH_URL = "https://jp.mercari.com/search?keyword=%E6%97%A7%E8%A3%8F%E5%88%9D%E7%89%88psa&order=desc&sort=created_time&status=on_sale"

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not installed. Mercari scraping disabled.")

    def search_listings(self, max_pages: int = 1) -> list[dict]:
        """Search for no-rarity PSA Pokemon cards on Mercari Japan."""
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not available. Skipping Mercari.")
            return []

        all_listings = []

        try:
            with sync_playwright() as p:
                # Use headless=False - Mercari detects headless browsers
                # Requires xvfb on Linux for GitHub Actions
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

                # Stealth scripts
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                    window.chrome = {runtime: {}};
                """)

                page = context.new_page()

                print("Fetching Mercari Japan...")

                try:
                    # Go directly to search URL
                    page.goto(self.SEARCH_URL, timeout=60000)

                    # Wait for any challenge to complete
                    for _ in range(6):
                        page.wait_for_timeout(5000)
                        title = page.title().lower()
                        if 'just a moment' not in title and 'checking' not in title:
                            break

                    page.wait_for_timeout(3000)

                    # Extract listings
                    listings = self._extract_listings(page)
                    if listings:
                        all_listings.extend(listings)
                        print(f"Found {len(listings)} Mercari Japan listings")
                    else:
                        print("No Mercari Japan listings found")

                except PlaywrightTimeout:
                    print("Timeout loading Mercari Japan")
                except Exception as e:
                    # Handle encoding errors in exception messages
                    error_msg = str(e).encode('ascii', 'replace').decode('ascii')
                    print(f"Error loading Mercari Japan: {error_msg}")

                browser.close()

        except Exception as e:
            print(f"Mercari scraper error: {e}")

        return all_listings

    def _extract_listings(self, page) -> list[dict]:
        """Extract listings from Mercari Japan search results page."""
        listings = []
        seen_ids = set()

        try:
            # Find all item links
            links = page.query_selector_all('a[href*="/item/"]')

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
                    seen_ids.add(item_id)

                    # Parse text content - handle encoding issues
                    try:
                        text = link.inner_text().strip()
                    except:
                        text = ""

                    lines = [l.strip() for l in text.split('\n') if l.strip()]

                    # Filter out price lines (SG$, numbers, etc.) to find the actual title
                    title_lines = [
                        l for l in lines
                        if not l.startswith('SG')
                        and not l.startswith('¥')
                        and not l.startswith('￥')
                        and not re.match(r'^[\d,\.]+$', l.replace(',', ''))
                    ]
                    title = title_lines[0][:100] if title_lines else item_id

                    # Find price (Japanese yen ¥/円, or SG$ for Singapore)
                    price = None
                    for line in lines:
                        # Match SG$1,234 or ¥1,234 or 1234円
                        price_match = re.search(r'(?:SG\$|[¥￥])?([\d,]+(?:\.\d{2})?)', line)
                        if price_match and (line.startswith('SG') or '¥' in line or '￥' in line or line[0].isdigit()):
                            try:
                                price = float(price_match.group(1).replace(',', ''))
                            except:
                                pass
                            break

                    full_link = href if href.startswith('http') else f"{self.BASE_URL}{href}"

                    listings.append({
                        'listing_id': item_id,
                        'item_id': item_id,
                        'title': title,
                        'price': price,
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
