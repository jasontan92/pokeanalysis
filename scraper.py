"""
eBay Listings Scraper for "No Rarity 1996" Pokemon Cards.
Supports both sold listings and active (live) listings.
"""

import re
import time
import random
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Optional

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class EbayScraper:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self._update_headers()

    def _update_headers(self):
        """Update session headers with a random user agent."""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        })

    def fetch_page(self, url, max_retries=3):
        """Fetch a page with retry logic and rate limiting."""
        for attempt in range(max_retries):
            try:
                # Random delay between requests (3-7 seconds)
                delay = random.uniform(3, 7)
                time.sleep(delay)

                # Rotate user agent occasionally
                if random.random() < 0.3:
                    self._update_headers()

                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = 60 * (attempt + 1)
                    print(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"HTTP {response.status_code} on attempt {attempt + 1}")

            except requests.RequestException as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(30)

        return None

    def parse_listings(self, html_content):
        """Parse eBay listings from HTML content."""
        soup = BeautifulSoup(html_content, 'lxml')
        listings = []

        # Try both layout types (s-item is more common for sold listings)
        items = soup.select('li.s-item')
        if not items:
            items = soup.select('li.s-card')

        for item in items:
            listing = self._parse_single_listing(item)
            if listing and listing.get('sold_date'):
                listings.append(listing)

        return listings

    def _parse_single_listing(self, item):
        """Extract data from a single listing element."""
        try:
            # Get title
            title_elem = item.select_one('.s-item__title')
            if not title_elem:
                title_elem = item.select_one('.s-card__title')
            title = title_elem.get_text(strip=True) if title_elem else None

            # Skip placeholder items
            if title and title.lower() == 'shop on ebay':
                return None

            # Get price
            price_elem = item.select_one('.s-item__price')
            if not price_elem:
                price_elem = item.select_one('.s-card__price')
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = self._parse_price(price_text)

            # Get sold date - look for "Sold" text
            item_text = item.get_text()
            sold_date = None

            # Pattern: "Sold Jan 19, 2026" or "Sold  Jan 19, 2026"
            date_match = re.search(r'Sold\s+(\w{3}\s+\d{1,2},\s+\d{4})', item_text)
            if date_match:
                sold_date = self._parse_date(date_match.group(1))

            # Get link
            link_elem = item.select_one('a.s-item__link')
            if not link_elem:
                link_elem = item.select_one('a')
            link = link_elem.get('href') if link_elem else None

            # Extract item ID
            item_id = self._extract_item_id(link)

            return {
                'item_id': item_id,
                'title': title,
                'price': price,
                'sold_date': sold_date,
                'link': link
            }

        except Exception as e:
            print(f"Error parsing listing: {e}")
            return None

    def _parse_price(self, price_text):
        """Convert price text to float."""
        if not price_text:
            return None
        # Handle ranges like "$10.00 to $20.00" - take first price
        match = re.search(r'\$?([\d,]+\.?\d*)', price_text.replace(',', ''))
        return float(match.group(1)) if match else None

    def _parse_date(self, date_string):
        """Convert 'Jan 19, 2026' to ISO date string."""
        try:
            dt = datetime.strptime(date_string.strip(), '%b %d, %Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return None

    def _extract_item_id(self, url: str) -> Optional[str]:
        """Extract eBay item ID from URL."""
        if not url:
            return None
        # Pattern: /itm/123456789 or /itm/title/123456789
        match = re.search(r'/itm/(?:[^/]+/)?(\d+)', url)
        if match:
            return match.group(1)
        # Also check query param
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'item' in params:
            return params['item'][0]
        return None

    def parse_active_listings(self, html_content):
        """Parse active (non-sold) eBay listings from HTML content."""
        soup = BeautifulSoup(html_content, 'lxml')
        listings = []

        items = soup.select('li.s-item')
        if not items:
            items = soup.select('li.s-card')

        for item in items:
            listing = self._parse_active_listing(item)
            if listing and listing.get('title'):
                listings.append(listing)

        return listings

    def _parse_active_listing(self, item):
        """Extract data from an active listing element."""
        try:
            # Get title
            title_elem = item.select_one('.s-item__title')
            if not title_elem:
                title_elem = item.select_one('.s-card__title')
            title = title_elem.get_text(strip=True) if title_elem else None

            # Skip placeholder items
            if title and title.lower() == 'shop on ebay':
                return None

            # Get price
            price_elem = item.select_one('.s-item__price')
            if not price_elem:
                price_elem = item.select_one('.s-card__price')
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = self._parse_price(price_text)

            # Get link
            link_elem = item.select_one('a.s-item__link')
            if not link_elem:
                link_elem = item.select_one('a')
            link = link_elem.get('href') if link_elem else None

            # Extract item ID
            item_id = self._extract_item_id(link)

            # Get listing type (auction, buy it now, etc)
            listing_type = "unknown"
            format_elem = item.select_one('.s-item__purchaseOptions, .s-item__dynamic')
            if format_elem:
                format_text = format_elem.get_text(strip=True).lower()
                if 'bid' in format_text or 'auction' in format_text:
                    listing_type = "auction"
                elif 'buy it now' in format_text:
                    listing_type = "buy_it_now"
                elif 'or best offer' in format_text:
                    listing_type = "best_offer"

            # Get time remaining for auctions
            time_left = None
            time_elem = item.select_one('.s-item__time-left, .s-item__time-end')
            if time_elem:
                time_left = time_elem.get_text(strip=True)

            return {
                'item_id': item_id,
                'title': title,
                'price': price,
                'listing_type': listing_type,
                'time_left': time_left,
                'link': link,
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error parsing active listing: {e}")
            return None

    def scrape_active_listings(self, search_term, max_pages=3, items_per_page=60):
        """Scrape active (live) listings sorted by newly listed.

        Args:
            search_term: Keywords to search for
            max_pages: Maximum pages to fetch (default 3 for monitoring)
            items_per_page: Items per page (60, 120, or 240)
        """
        # Sort by newly listed (_sop=10)
        base_url = (
            f"https://www.ebay.com/sch/i.html?"
            f"_nkw={search_term.replace(' ', '+')}&"
            f"_sacat=0&"
            f"_sop=10&"  # Sort by newly listed
            f"_ipg={items_per_page}"
        )

        all_listings = []
        page = 1

        print(f"Scraping eBay active listings for: '{search_term}'")

        while page <= max_pages:
            url = f"{base_url}&_pgn={page}"
            print(f"Fetching active listings page {page}...")

            html = self.fetch_page(url)
            if not html:
                print(f"Failed to fetch page {page}, stopping.")
                break

            listings = self.parse_active_listings(html)

            if not listings:
                print(f"No more listings found on page {page}.")
                break

            all_listings.extend(listings)
            print(f"Found {len(listings)} active listings on page {page} (total: {len(all_listings)})")

            page += 1

        return all_listings

    def scrape_all_pages(self, search_term, max_pages=30, items_per_page=240):
        """Scrape all pages of sold listings for a search term.

        Args:
            search_term: Keywords to search for
            max_pages: Maximum pages to fetch
            items_per_page: Items per page (60, 120, or 240)
        """
        base_url = (
            f"https://www.ebay.com/sch/i.html?"
            f"_nkw={search_term.replace(' ', '+')}&"
            f"_sacat=0&LH_Sold=1&LH_Complete=1&"
            f"_ipg={items_per_page}"
        )

        all_listings = []
        page = 1

        print(f"Scraping eBay sold listings for: '{search_term}'")

        while page <= max_pages:
            url = f"{base_url}&_pgn={page}"
            print(f"Fetching page {page}...")

            html = self.fetch_page(url)
            if not html:
                print(f"Failed to fetch page {page}, stopping.")
                break

            listings = self.parse_listings(html)

            if not listings:
                print(f"No more listings found on page {page}.")
                break

            all_listings.extend(listings)
            print(f"Found {len(listings)} listings on page {page} (total: {len(all_listings)})")

            page += 1

        return all_listings

    def save_to_json(self, listings, filepath):
        """Save listings to JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(listings, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(listings)} listings to {filepath}")


if __name__ == '__main__':
    # Test the scraper
    scraper = EbayScraper()
    listings = scraper.scrape_all_pages("no rarity 1996", max_pages=5)
    print(f"\nTotal listings scraped: {len(listings)}")

    if listings:
        print("\nSample listing:")
        print(json.dumps(listings[0], indent=2))
