"""
Mercari Marketplace Scraper using Playwright.
Note: Mercari has anti-bot protection - this may get blocked intermittently.
"""

import re
import json
import hashlib
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class MercariScraper:
    """Scraper for Mercari marketplace using Playwright."""

    BASE_URL = "https://www.mercari.com"

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not installed. Mercari scraping disabled.")

    def search_listings(self, search_term: str, max_pages: int = 2) -> list[dict]:
        """Search for listings on Mercari."""
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not available. Skipping Mercari.")
            return []

        all_listings = []
        search_query = quote_plus(search_term)

        try:
            with sync_playwright() as p:
                # Use non-headless with stealth settings to avoid detection
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                    ]
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                )

                # Add stealth scripts
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                """)

                page = context.new_page()

                print(f"Fetching Mercari: {search_term}")

                for page_num in range(1, max_pages + 1):
                    # Mercari search URL - sorted by newest
                    url = f"{self.BASE_URL}/search/?keyword={search_query}&sortBy=2"
                    if page_num > 1:
                        # Mercari uses different pagination
                        url = f"{self.BASE_URL}/search/?keyword={search_query}&sortBy=2&page={page_num}"

                    try:
                        page.goto(url, timeout=30000, wait_until='networkidle')
                        page.wait_for_timeout(3000)

                        # Check if we got blocked
                        if 'blocked' in page.url.lower() or 'captcha' in page.content().lower():
                            print("Mercari blocked request (captcha/block detected)")
                            break

                    except PlaywrightTimeout:
                        print(f"Timeout loading Mercari page {page_num}")
                        break
                    except Exception as e:
                        print(f"Error loading Mercari: {e}")
                        break

                    # Extract listings
                    listings = self._extract_listings(page)

                    if not listings:
                        print(f"No listings found on Mercari page {page_num}")
                        break

                    all_listings.extend(listings)
                    print(f"Found {len(listings)} Mercari listings on page {page_num}")

                browser.close()

        except Exception as e:
            print(f"Mercari scraper error: {e}")

        return all_listings

    def _extract_listings(self, page) -> list[dict]:
        """Extract listings from Mercari search results page."""
        listings = []
        seen_ids = set()

        try:
            # Try to find product cards - Mercari uses data-testid attributes
            # Look for item cards in the search results
            cards = page.query_selector_all('[data-testid="ItemContainer"], [data-testid="SearchResults"] a, div[class*="ItemCard"], a[href*="/item/"]')

            if not cards:
                # Fallback: try to parse from page text
                return self._extract_from_text(page)

            for card in cards:
                try:
                    listing = self._parse_card(card)
                    if listing and listing['listing_id'] not in seen_ids:
                        seen_ids.add(listing['listing_id'])
                        listings.append(listing)
                except Exception:
                    continue

        except Exception as e:
            print(f"Error extracting Mercari listings: {e}")

        return listings

    def _parse_card(self, card) -> Optional[dict]:
        """Parse a single Mercari item card."""
        try:
            # Get link/href for item ID
            href = card.get_attribute('href')
            if not href:
                link_elem = card.query_selector('a[href*="/item/"]')
                href = link_elem.get_attribute('href') if link_elem else None

            if not href or '/item/' not in href:
                return None

            # Extract item ID from URL
            item_match = re.search(r'/item/([a-zA-Z0-9]+)', href)
            if not item_match:
                return None

            item_id = f"mercari-{item_match.group(1)}"

            # Get title
            title = None
            title_elem = card.query_selector('[data-testid="ItemName"], [class*="ItemName"], p, span')
            if title_elem:
                title = title_elem.inner_text().strip()

            if not title:
                title = card.inner_text().split('\n')[0].strip()[:100]

            if not title or len(title) < 5:
                return None

            # Get price
            price = None
            price_elem = card.query_selector('[data-testid="ItemPrice"], [class*="Price"], span[class*="price"]')
            if price_elem:
                price_text = price_elem.inner_text()
                price_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', price_text.replace(',', ''))
                if price_match:
                    try:
                        price = float(price_match.group(1))
                    except:
                        pass

            # Build full link
            link = href if href.startswith('http') else f"{self.BASE_URL}{href}"

            return {
                'listing_id': item_id,
                'item_id': item_id,
                'title': title,
                'price': price,
                'listing_type': 'buy_now',
                'link': link,
                'platform': 'mercari',
                'scraped_at': datetime.now().isoformat()
            }

        except Exception:
            return None

    def _extract_from_text(self, page) -> list[dict]:
        """Fallback: extract listings by parsing page text."""
        listings = []
        seen_titles = set()

        try:
            # Get all links that look like item links
            links = page.query_selector_all('a[href*="/item/"]')

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue

                    item_match = re.search(r'/item/([a-zA-Z0-9]+)', href)
                    if not item_match:
                        continue

                    item_id = f"mercari-{item_match.group(1)}"

                    # Get text content
                    text = link.inner_text().strip()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]

                    if not lines:
                        continue

                    # First line is usually title
                    title = lines[0][:100]

                    # Skip if too short or already seen
                    if len(title) < 10 or title[:50] in seen_titles:
                        continue

                    seen_titles.add(title[:50])

                    # Find price in text
                    price = None
                    for line in lines:
                        price_match = re.search(r'\$(\d+(?:\.\d{2})?)', line)
                        if price_match:
                            try:
                                price = float(price_match.group(1))
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
                        'platform': 'mercari',
                        'scraped_at': datetime.now().isoformat()
                    })

                except Exception:
                    continue

        except Exception as e:
            print(f"Error in text extraction: {e}")

        return listings


if __name__ == '__main__':
    scraper = MercariScraper()
    print("Testing Mercari search...")
    listings = scraper.search_listings("1996 pokemon no rarity", max_pages=1)
    print(f"\nTotal listings found: {len(listings)}")
    for listing in listings[:5]:
        print(json.dumps(listing, indent=2))
