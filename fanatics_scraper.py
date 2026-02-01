"""
Fanatics Collect Marketplace Scraper using Playwright.
Handles JavaScript-rendered content.
"""

import re
import json
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class FanaticsScraper:
    """Scraper for Fanatics Collect marketplace using Playwright."""

    BASE_URL = "https://www.fanaticscollect.com"

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not installed. Fanatics scraping disabled.")

    def search_listings(self, search_term: str, max_pages: int = 5) -> list[dict]:
        """Search for listings on Fanatics Collect marketplace (both auction and buy now)."""
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not available. Skipping Fanatics.")
            return []

        all_listings = []
        search_query = quote_plus(search_term)

        # Search both WEEKLY (auctions) and FIXED (buy now) listings
        listing_types = [
            ("WEEKLY", "auction"),   # Auctions
            ("FIXED", "buy_now"),    # Buy Now
        ]

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                cookie_closed = False

                for type_param, type_name in listing_types:
                    type_listings = []
                    seen_ids = set()  # Track IDs across pages to avoid duplicates

                    for page_num in range(1, max_pages + 1):
                        url = f"{self.BASE_URL}/marketplace?q={search_query}&type={type_param}&page={page_num}"

                        if page_num == 1:
                            print(f"Fetching Fanatics {type_name}: {search_term}")

                        try:
                            page.goto(url, timeout=60000)

                            # Close cookie popup once, then reload to ensure page renders fully
                            if not cookie_closed:
                                try:
                                    page.click('text=Accept all', timeout=3000)
                                    cookie_closed = True
                                    page.wait_for_timeout(1000)
                                    # Reload the page after dismissing cookie popup
                                    page.goto(url, timeout=60000)
                                except:
                                    pass

                            page.wait_for_timeout(2000)

                        except PlaywrightTimeout:
                            print(f"Timeout loading Fanatics {type_name} page {page_num}")
                            break

                        # Extract listings from this page
                        listings = self._extract_listings_from_page(page, search_term)

                        # Filter out duplicates we've seen on previous pages
                        new_listings = []
                        for listing in listings:
                            if listing['listing_id'] not in seen_ids:
                                seen_ids.add(listing['listing_id'])
                                listing['listing_type'] = type_name
                                new_listings.append(listing)

                        if not new_listings:
                            break  # No more new results

                        type_listings.extend(new_listings)

                    all_listings.extend(type_listings)
                    print(f"Found {len(type_listings)} Fanatics {type_name} listings")

                browser.close()

        except Exception as e:
            print(f"Fanatics scraper error: {e}")

        return all_listings

    def _extract_listings_from_page(self, page, search_term: str) -> list[dict]:
        """Extract listings by parsing full page text with regex."""
        listings = []
        seen_titles = set()

        # Get full page text
        full_text = page.inner_text('body')

        # Find all Pokemon card titles (lines starting with year or containing "Pokemon")
        # Format: Title on one line, price ($X,XXX) on next or same line
        lines = full_text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if this is a Pokemon card title
            if '1996 Pokemon' in line or ('Pokemon' in line and ('PSA' in line or 'CGC' in line or 'BGS' in line)):
                title = line

                # Look for price in next few lines
                price = None
                for j in range(i + 1, min(i + 5, len(lines))):
                    price_match = re.search(r'\$?([\d,]+)(?:\.\d{2})?', lines[j])
                    if price_match and lines[j].strip().replace(',', '').replace('$', '').replace('.', '').isdigit():
                        try:
                            price = float(price_match.group(1).replace(',', ''))
                            break
                        except:
                            pass
                    # Also check for standalone price
                    if lines[j].strip().startswith('$'):
                        price_text = lines[j].strip().replace('$', '').replace(',', '').split()[0]
                        try:
                            price = float(price_text)
                            break
                        except:
                            pass

                # Deduplicate by title
                title_key = title[:60]
                if title_key not in seen_titles:
                    seen_titles.add(title_key)

                    # Generate ID from title hash
                    listing_id = f"fc-{abs(hash(title)) % 10000000}"

                    listings.append({
                        'listing_id': listing_id,
                        'title': title,
                        'price': price,
                        'listing_type': 'buy_now',  # Will be overridden by caller
                        'time_left': None,
                        'link': f"{self.BASE_URL}/marketplace?q={quote_plus(search_term)}",
                        'platform': 'fanatics',
                        'scraped_at': datetime.now().isoformat()
                    })

            i += 1

        return listings

    def _extract_listings_from_text(self, page, search_term: str) -> list[dict]:
        """Extract listings by parsing page text content (legacy method)."""
        listings = []
        seen_titles = set()

        # Find all divs that might be product cards
        cards = page.query_selector_all('div')

        for card in cards:
            try:
                text = card.inner_text()

                # Filter: must have price, reasonable length, and search terms
                if '$' not in text:
                    continue
                if len(text) < 30 or len(text) > 600:
                    continue

                text_lower = text.lower()
                # Must match search terms somewhat
                search_words = search_term.lower().split()
                if not any(word in text_lower for word in search_words):
                    continue

                # Parse the card text
                listing = self._parse_card_text(text)

                if listing and listing.get('title'):
                    # Deduplicate by title
                    title_key = listing['title'][:50]
                    if title_key not in seen_titles:
                        seen_titles.add(title_key)
                        listings.append(listing)

            except Exception:
                continue

        return listings

    def _parse_card_text(self, text: str) -> Optional[dict]:
        """Parse card text content into listing dict."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        if len(lines) < 2:
            return None

        # Find title - usually the longest descriptive line
        title = None
        for line in lines:
            if len(line) > 30 and ('pokemon' in line.lower() or 'psa' in line.lower() or '1996' in line.lower()):
                title = line
                break

        if not title:
            # Take first long line
            for line in lines:
                if len(line) > 20 and not line.startswith('$'):
                    title = line
                    break

        if not title:
            return None

        # Find price
        price = None
        for line in lines:
            match = re.search(r'\$[\d,]+\.?\d*', line)
            if match:
                price_text = match.group().replace('$', '').replace(',', '')
                try:
                    price = float(price_text)
                except:
                    pass
                break

        # Find lot number as ID
        listing_id = None
        for line in lines:
            lot_match = re.search(r'LOT[:\s]*(\d+)', line, re.IGNORECASE)
            if lot_match:
                listing_id = f"lot-{lot_match.group(1)}"
                break

        if not listing_id:
            # Generate ID from title hash
            listing_id = f"fc-{abs(hash(title)) % 1000000}"

        # Check if it's an auction
        listing_type = "auction" if 'bid' in text.lower() else "buy_now"

        # Get time left
        time_left = None
        time_match = re.search(r'(\d+[hd])\s*(\d+m)?', text)
        if time_match:
            time_left = time_match.group(0).strip()

        return {
            'listing_id': listing_id,
            'title': title,
            'price': price,
            'listing_type': listing_type,
            'time_left': time_left,
            'link': f"{self.BASE_URL}/marketplace?q={quote_plus(title[:30])}",
            'platform': 'fanatics',
            'scraped_at': datetime.now().isoformat()
        }

    def get_sales_history(self, search_term: str, max_pages: int = 1) -> list[dict]:
        """Fetch sales history - not implemented yet."""
        return []


if __name__ == '__main__':
    scraper = FanaticsScraper()
    print("Testing Fanatics Collect search...")
    listings = scraper.search_listings("1996 no rarity", max_pages=5)
    print(f"\nTotal listings found: {len(listings)}")
    for listing in listings[:3]:
        print(json.dumps(listing, indent=2))
