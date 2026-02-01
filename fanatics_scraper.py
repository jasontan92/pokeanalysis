"""
Fanatics Collect Marketplace Scraper.
Scrapes listings from fanaticscollect.com (formerly PWCC).
"""

import re
import time
import random
import json
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode, quote_plus

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from config import Config


class FanaticsScraper:
    """Scraper for Fanatics Collect marketplace."""

    BASE_URL = "https://www.fanaticscollect.com"
    SEARCH_URL = f"{BASE_URL}/marketplace"

    def __init__(self, email: str = None, password: str = None):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.email = email or Config.FANATICS_EMAIL
        self.password = password or Config.FANATICS_PASSWORD
        self.authenticated = False
        self._update_headers()

    def _update_headers(self):
        """Update session headers with a random user agent."""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def authenticate(self) -> bool:
        """
        Attempt to authenticate with Fanatics Collect.
        Note: This may need adjustment based on their actual auth flow.
        """
        if not self.email or not self.password:
            print("Fanatics credentials not configured. Proceeding without auth.")
            return False

        try:
            # First get the login page to get any CSRF tokens
            login_page = self.session.get(f"{self.BASE_URL}/login", timeout=30)
            if login_page.status_code != 200:
                print(f"Failed to load login page: {login_page.status_code}")
                return False

            # Parse for CSRF token if present
            soup = BeautifulSoup(login_page.text, 'lxml')
            csrf_token = None
            csrf_input = soup.select_one('input[name="csrf_token"], input[name="_token"]')
            if csrf_input:
                csrf_token = csrf_input.get('value')

            # Attempt login
            login_data = {
                'email': self.email,
                'password': self.password,
            }
            if csrf_token:
                login_data['csrf_token'] = csrf_token

            response = self.session.post(
                f"{self.BASE_URL}/login",
                data=login_data,
                timeout=30,
                allow_redirects=True
            )

            # Check if login was successful
            if response.status_code == 200 and 'logout' in response.text.lower():
                print("Successfully authenticated with Fanatics Collect")
                self.authenticated = True
                return True
            else:
                print("Authentication may have failed. Proceeding anyway.")
                return False

        except requests.RequestException as e:
            print(f"Authentication error: {e}")
            return False

    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch a page with retry logic and rate limiting."""
        for attempt in range(max_retries):
            try:
                # Random delay between requests
                delay = random.uniform(2, 5)
                time.sleep(delay)

                # Rotate user agent occasionally
                if random.random() < 0.3:
                    self._update_headers()

                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:
                    wait_time = 60 * (attempt + 1)
                    print(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif response.status_code == 403:
                    print("Access forbidden. May need authentication.")
                    if not self.authenticated and self.email:
                        self.authenticate()
                else:
                    print(f"HTTP {response.status_code} on attempt {attempt + 1}")

            except requests.RequestException as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(30)

        return None

    def search_listings(self, search_term: str, max_pages: int = 2) -> list[dict]:
        """
        Search for listings on Fanatics Collect marketplace.

        Args:
            search_term: Keywords to search for
            max_pages: Maximum pages to fetch

        Returns:
            List of listing dictionaries
        """
        all_listings = []

        # Build search URL
        search_query = quote_plus(search_term)

        for page in range(1, max_pages + 1):
            # Fanatics Collect marketplace search URL pattern
            url = f"{self.SEARCH_URL}?q={search_query}&page={page}"
            print(f"Fetching Fanatics Collect page {page}...")

            html = self.fetch_page(url)
            if not html:
                print(f"Failed to fetch page {page}")
                break

            listings = self._parse_listings(html)

            if not listings:
                print(f"No more listings found on page {page}")
                break

            all_listings.extend(listings)
            print(f"Found {len(listings)} listings on page {page} (total: {len(all_listings)})")

        return all_listings

    def _parse_listings(self, html_content: str) -> list[dict]:
        """Parse listings from Fanatics Collect HTML."""
        soup = BeautifulSoup(html_content, 'lxml')
        listings = []

        # Try various possible selectors for listing cards
        # These may need adjustment based on actual site structure
        selectors = [
            'div[data-testid="listing-card"]',
            'div.listing-card',
            'div.product-card',
            'article.listing',
            'div[class*="ListingCard"]',
            'a[href*="/marketplace/listing/"]',
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break

        if not items:
            # Fallback: look for links to listings
            items = soup.select('a[href*="/listing/"]')

        for item in items:
            listing = self._parse_single_listing(item, soup)
            if listing:
                listings.append(listing)

        return listings

    def _parse_single_listing(self, item, full_soup) -> Optional[dict]:
        """Extract data from a single listing element."""
        try:
            # Get title
            title = None
            title_selectors = [
                '.listing-title',
                '.product-title',
                'h3',
                'h4',
                '[class*="title"]',
            ]
            for sel in title_selectors:
                title_elem = item.select_one(sel)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break

            if not title:
                # If item is a link, get text content
                if item.name == 'a':
                    title = item.get_text(strip=True)

            if not title:
                return None

            # Get price
            price = None
            price_selectors = [
                '.price',
                '.listing-price',
                '[class*="price"]',
                'span[class*="Price"]',
            ]
            for sel in price_selectors:
                price_elem = item.select_one(sel)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price:
                        break

            # Get link
            link = None
            if item.name == 'a':
                link = item.get('href')
            else:
                link_elem = item.select_one('a[href*="/listing/"], a[href*="/marketplace/"]')
                if link_elem:
                    link = link_elem.get('href')

            if link and not link.startswith('http'):
                link = f"{self.BASE_URL}{link}"

            # Extract listing ID from URL
            listing_id = self._extract_listing_id(link)

            # Get listing type (auction vs buy now)
            listing_type = "unknown"
            item_text = item.get_text().lower()
            if 'auction' in item_text or 'bid' in item_text:
                listing_type = "auction"
            elif 'buy now' in item_text or 'buy it now' in item_text:
                listing_type = "buy_now"

            # Get end time if auction
            end_time = None
            time_elem = item.select_one('[class*="time"], [class*="countdown"]')
            if time_elem:
                end_time = time_elem.get_text(strip=True)

            return {
                'listing_id': listing_id,
                'title': title,
                'price': price,
                'listing_type': listing_type,
                'end_time': end_time,
                'link': link,
                'platform': 'fanatics',
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error parsing Fanatics listing: {e}")
            return None

    def _parse_price(self, price_text: str) -> Optional[float]:
        """Convert price text to float."""
        if not price_text:
            return None
        match = re.search(r'\$?([\d,]+\.?\d*)', price_text.replace(',', ''))
        return float(match.group(1)) if match else None

    def _extract_listing_id(self, url: str) -> Optional[str]:
        """Extract listing ID from Fanatics URL."""
        if not url:
            return None
        # Pattern: /listing/12345 or /marketplace/listing/12345
        match = re.search(r'/listing/(\d+)', url)
        if match:
            return match.group(1)
        # Try to get any ID from the URL
        match = re.search(r'/(\d{5,})', url)
        return match.group(1) if match else None

    def get_sales_history(self, search_term: str, max_pages: int = 2) -> list[dict]:
        """
        Fetch sales history from sales-history.fanaticscollect.com

        Args:
            search_term: Keywords to search for
            max_pages: Maximum pages to fetch

        Returns:
            List of sold listing dictionaries
        """
        all_sales = []
        search_query = quote_plus(search_term)
        base_url = "https://sales-history.fanaticscollect.com"

        for page in range(1, max_pages + 1):
            url = f"{base_url}/search?q={search_query}&page={page}"
            print(f"Fetching Fanatics sales history page {page}...")

            html = self.fetch_page(url)
            if not html:
                break

            sales = self._parse_sales_history(html)
            if not sales:
                break

            all_sales.extend(sales)
            print(f"Found {len(sales)} sales on page {page} (total: {len(all_sales)})")

        return all_sales

    def _parse_sales_history(self, html_content: str) -> list[dict]:
        """Parse sales history listings."""
        soup = BeautifulSoup(html_content, 'lxml')
        sales = []

        # Try to find sale entries
        items = soup.select('div.sale-item, tr.sale-row, div[class*="sale"], a[href*="/sale/"]')

        for item in items:
            try:
                title = None
                price = None
                sold_date = None
                link = None

                # Extract title
                title_elem = item.select_one('.title, h3, h4, [class*="title"]')
                if title_elem:
                    title = title_elem.get_text(strip=True)

                # Extract price
                price_elem = item.select_one('.price, [class*="price"]')
                if price_elem:
                    price = self._parse_price(price_elem.get_text())

                # Extract date
                date_elem = item.select_one('.date, [class*="date"], time')
                if date_elem:
                    sold_date = date_elem.get_text(strip=True)

                # Extract link
                if item.name == 'a':
                    link = item.get('href')
                else:
                    link_elem = item.select_one('a')
                    if link_elem:
                        link = link_elem.get('href')

                if title:
                    sales.append({
                        'listing_id': self._extract_listing_id(link),
                        'title': title,
                        'price': price,
                        'sold_date': sold_date,
                        'link': link,
                        'platform': 'fanatics',
                        'scraped_at': datetime.now().isoformat()
                    })

            except Exception as e:
                continue

        return sales


if __name__ == '__main__':
    # Test the scraper
    scraper = FanaticsScraper()

    print("Testing Fanatics Collect marketplace search...")
    listings = scraper.search_listings("1996 no rarity", max_pages=1)
    print(f"\nTotal listings found: {len(listings)}")

    if listings:
        print("\nSample listing:")
        print(json.dumps(listings[0], indent=2))
