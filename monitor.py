#!/usr/bin/env python3
"""
Listing Monitor for Pokemon Cards.
Checks eBay and Fanatics Collect for new "1996 no rarity" listings.
Sends Telegram alerts for new items.

Run via cron every 30 minutes:
*/30 * * * * cd /path/to/pokeanalysis && python3 monitor.py >> /var/log/pokeanalysis.log 2>&1
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from config import Config
from scraper import EbayScraper
from fanatics_scraper import FanaticsScraper
from mercari_scraper import MercariScraper
from notifier import TelegramNotifier


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Config.LOG_FILE, mode='a')
    ]
)
logger = logging.getLogger(__name__)


class StateManager:
    """Manages seen listings state to avoid duplicate alerts."""

    def __init__(self, state_file: Path = None):
        self.state_file = state_file or Config.SEEN_LISTINGS_FILE
        self.state = self._load_state()
        self.is_first_run = self.state.get('last_check') is None

    def _load_state(self) -> dict:
        """Load state from JSON file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load state: {e}. Starting fresh.")

        return {
            'ebay_active': {},
            'ebay_sold': {},
            'fanatics_active': {},
            'fanatics_sold': {},
            'mercari_active': {},
            'ending_soon_alerted': {},  # Track auctions we've sent ending-soon alerts for
            'last_check': None,
            'last_heartbeat': None  # Track daily heartbeat
        }

    def save_state(self):
        """Save state to JSON file."""
        self.state['last_check'] = datetime.now().isoformat()
        self._cleanup_old_entries()

        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2)

        logger.info(f"State saved to {self.state_file}")

    def _cleanup_old_entries(self, days: int = 30):
        """Remove entries older than specified days to prevent file bloat."""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()

        for category in ['ebay_active', 'ebay_sold', 'fanatics_active', 'fanatics_sold', 'mercari_active', 'ending_soon_alerted']:
            if category in self.state and isinstance(self.state[category], dict):
                self.state[category] = {
                    k: v for k, v in self.state[category].items()
                    if v > cutoff_str
                }

    def is_new(self, category: str, listing_id: str) -> bool:
        """Check if a listing is new (not seen before)."""
        if not listing_id:
            return True  # Can't track without ID, treat as new
        return listing_id not in self.state.get(category, {})

    def mark_seen(self, category: str, listing_id: str):
        """Mark a listing as seen."""
        if not listing_id:
            return
        if category not in self.state:
            self.state[category] = {}
        self.state[category][listing_id] = datetime.now().isoformat()


class ListingMonitor:
    """Main monitoring orchestrator."""

    def __init__(self):
        self.state = StateManager()
        self.notifier = TelegramNotifier()
        self.ebay_scraper = EbayScraper()
        self.fanatics_scraper = FanaticsScraper()
        self.mercari_scraper = MercariScraper()
        self.search_term = Config.SEARCH_TERM
        self.target_pokemon = Config.TARGET_POKEMON

    def _matches_target_pokemon(self, title: str) -> bool:
        """Check if listing title contains any target Pokemon name."""
        if not title:
            return False
        title_lower = title.lower()
        return any(pokemon in title_lower for pokemon in self.target_pokemon)

    def _parse_time_left_minutes(self, time_left: str) -> Optional[int]:
        """
        Parse time_left string and return total minutes remaining.
        Handles formats like: "30m", "1h 30m", "2d 5h", "5h 23m 15s"
        Returns None if can't parse.
        """
        if not time_left:
            return None

        import re
        time_left = time_left.lower().strip()

        # Extract days, hours, minutes
        days = 0
        hours = 0
        minutes = 0

        day_match = re.search(r'(\d+)\s*d', time_left)
        hour_match = re.search(r'(\d+)\s*h', time_left)
        min_match = re.search(r'(\d+)\s*m', time_left)

        if day_match:
            days = int(day_match.group(1))
        if hour_match:
            hours = int(hour_match.group(1))
        if min_match:
            minutes = int(min_match.group(1))

        total_minutes = days * 24 * 60 + hours * 60 + minutes

        # If we couldn't parse anything meaningful, return None
        if total_minutes == 0 and not any([day_match, hour_match, min_match]):
            return None

        return total_minutes

    def _is_ending_soon(self, time_left: str, threshold_minutes: int = 30) -> bool:
        """Check if auction is ending within threshold minutes."""
        minutes = self._parse_time_left_minutes(time_left)
        if minutes is None:
            return False
        return minutes <= threshold_minutes and minutes > 0

    def _should_send_heartbeat(self) -> bool:
        """Check if we should send a daily heartbeat (once per 24 hours)."""
        last_heartbeat = self.state.state.get('last_heartbeat')
        if not last_heartbeat:
            return True

        try:
            last_dt = datetime.fromisoformat(last_heartbeat)
            hours_since = (datetime.now() - last_dt).total_seconds() / 3600
            return hours_since >= 24
        except (ValueError, TypeError):
            return True

    def _send_heartbeat(self):
        """Send daily heartbeat message to confirm bot is running."""
        if not self._should_send_heartbeat():
            return

        message = (
            "💚 <b>Monitor Active</b>\n\n"
            f"Daily check-in at {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            "Watching for: 1996 No Rarity Pokemon + CoroCoro Glossy Pikachu/Jigglypuff"
        )

        if self.notifier.send_message(message):
            self.state.state['last_heartbeat'] = datetime.now().isoformat()
            logger.info("Daily heartbeat sent")

    def _check_ending_soon_auctions(self, listings: list[dict]):
        """
        Check listings for auctions ending soon and send alerts.
        Only alerts once per auction (tracked in ending_soon_alerted state).
        """
        for listing in listings:
            # Only check auctions
            if listing.get('listing_type') != 'auction':
                continue

            listing_id = listing.get('item_id') or listing.get('listing_id')
            if not listing_id:
                continue

            # Check if matches target pokemon filter
            title = listing.get('title', '')
            if not self._matches_target_pokemon(title):
                continue

            # Check if ending soon
            time_left = listing.get('time_left', '')
            if not self._is_ending_soon(time_left):
                continue

            # Check if we already sent an ending-soon alert for this auction
            if not self.state.is_new('ending_soon_alerted', listing_id):
                continue

            # Send ending-soon alert
            logger.info(f"Auction ending soon: {title[:50]} ({time_left})")

            success = self.notifier.send_listing_alert(
                platform='eBay',
                title=title,
                price=listing.get('price'),
                link=listing.get('link', ''),
                listing_type='ENDING',
                time_left=time_left
            )

            if success:
                # Mark as alerted so we don't alert again
                self.state.mark_seen('ending_soon_alerted', listing_id)
                logger.info(f"Ending soon alert sent for {listing_id}")

    def run(self):
        """Run the full monitoring cycle."""
        logger.info("=" * 50)
        logger.info(f"Starting monitor run at {datetime.now()}")
        logger.info(f"Search term: {self.search_term}")

        # Validate configuration
        missing = Config.validate()
        if missing:
            logger.warning(f"Missing configuration: {', '.join(missing)}")
            logger.warning("Telegram notifications will be disabled.")

        # Send daily heartbeat (once per 24 hours)
        self._send_heartbeat()

        # First run notification
        if self.state.is_first_run:
            logger.info("First run detected - will send alerts for most recent listings only")
            self.notifier.send_message(
                "🔄 <b>Monitor Started</b>\n\n"
                "Sending alerts for recent listings.\n"
                "Future runs will only alert on NEW listings."
            )

        new_listings = []
        sold_listings = []

        try:
            # 1. Scrape eBay active listings
            logger.info("Checking eBay active listings...")
            ebay_active = self.ebay_scraper.scrape_active_listings(
                self.search_term, max_pages=2
            )
            new_ebay_active = self._process_listings(
                ebay_active, 'ebay_active', 'eBay', 'NEW'
            )
            new_listings.extend(new_ebay_active)

            # 1b. Check for auctions ending soon (within 30 minutes)
            # Scrape separately sorted by ending soonest, since active listings
            # are sorted by newly listed and miss auctions about to end
            logger.info("Checking eBay auctions ending soon...")
            ebay_ending_soon = self.ebay_scraper.scrape_ending_soon(
                self.search_term, max_pages=1
            )
            self._check_ending_soon_auctions(ebay_ending_soon)

            # 2. Scrape eBay sold listings
            logger.info("Checking eBay sold listings...")
            ebay_sold = self.ebay_scraper.scrape_all_pages(
                self.search_term, max_pages=1
            )
            new_ebay_sold = self._process_listings(
                ebay_sold, 'ebay_sold', 'eBay', 'SOLD'
            )
            sold_listings.extend(new_ebay_sold)

            # 3. Scrape Fanatics Collect active listings
            logger.info("Checking Fanatics Collect marketplace...")
            fanatics_active = self.fanatics_scraper.search_listings(
                self.search_term, max_pages=5
            )
            new_fanatics_active = self._process_listings(
                fanatics_active, 'fanatics_active', 'Fanatics', 'NEW'
            )
            new_listings.extend(new_fanatics_active)

            # 4. Scrape Fanatics sales history
            logger.info("Checking Fanatics sales history...")
            fanatics_sold = self.fanatics_scraper.get_sales_history(
                self.search_term, max_pages=1
            )
            new_fanatics_sold = self._process_listings(
                fanatics_sold, 'fanatics_sold', 'Fanatics', 'SOLD'
            )
            sold_listings.extend(new_fanatics_sold)

            # 5. Scrape Mercari Japan listings (旧裏初版psa = no rarity PSA cards)
            logger.info("Checking Mercari Japan marketplace...")
            mercari_active = self.mercari_scraper.search_listings()

            # Debug: Log sample Mercari titles and filter matches
            if mercari_active:
                logger.info(f"Mercari debug - checking {len(mercari_active)} listings against filter")
                for i, listing in enumerate(mercari_active[:5]):
                    title = listing.get('title', '')
                    # Safely encode title for logging
                    safe_title = title.encode('ascii', 'replace').decode('ascii')[:60]
                    matches = self._matches_target_pokemon(title)
                    logger.info(f"Mercari [{i}]: '{safe_title}' -> matches={matches}")

            new_mercari_active = self._process_listings(
                mercari_active, 'mercari_active', 'Mercari', 'NEW'
            )
            new_listings.extend(new_mercari_active)

            # ----------------------------------------------------------
            # 6-8. CoroCoro glossy Pikachu & Jigglypuff (separate search
            #       queries since the NR search term won't find these)
            # ----------------------------------------------------------

            # 6. eBay - CoroCoro glossy searches
            for term in Config.COROCORO_EBAY_TERMS:
                logger.info(f"Checking eBay CoroCoro: '{term}'...")
                cc_ebay_active = self.ebay_scraper.scrape_active_listings(
                    term, max_pages=1
                )
                new_cc_ebay = self._process_listings(
                    cc_ebay_active, 'ebay_active', 'eBay', 'NEW'
                )
                new_listings.extend(new_cc_ebay)

                # Also check ending-soon auctions
                cc_ebay_ending = self.ebay_scraper.scrape_ending_soon(
                    term, max_pages=1
                )
                self._check_ending_soon_auctions(cc_ebay_ending)

            # 7. Fanatics - CoroCoro searches
            for term in Config.COROCORO_FANATICS_TERMS:
                logger.info(f"Checking Fanatics CoroCoro: '{term}'...")
                cc_fanatics = self.fanatics_scraper.search_listings(
                    term, max_pages=2
                )
                new_cc_fanatics = self._process_listings(
                    cc_fanatics, 'fanatics_active', 'Fanatics', 'NEW'
                )
                new_listings.extend(new_cc_fanatics)

            # 8. Mercari Japan - CoroCoro searches (Japanese keywords)
            for keyword in Config.COROCORO_MERCARI_KEYWORDS:
                safe_kw = keyword.encode('ascii', 'replace').decode('ascii')
                logger.info(f"Checking Mercari CoroCoro: '{safe_kw}'...")
                cc_mercari = self.mercari_scraper.search_listings(
                    keyword=keyword
                )
                new_cc_mercari = self._process_listings(
                    cc_mercari, 'mercari_active', 'Mercari', 'NEW'
                )
                new_listings.extend(new_cc_mercari)

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            self.notifier.send_error(f"Scraping error: {str(e)[:200]}")

        # Save updated state
        self.state.save_state()

        # Log summary
        logger.info(f"Run complete. New: {len(new_listings)}, Sold: {len(sold_listings)}")
        logger.info("=" * 50)

        return new_listings, sold_listings

    # Max alerts to send on first run (most recent listings only)
    FIRST_RUN_ALERT_LIMIT = 20

    def _process_listings(
        self,
        listings: list[dict],
        category: str,
        platform: str,
        listing_type: str
    ) -> list[dict]:
        """
        Process listings: filter new ones and send alerts.

        Args:
            listings: List of scraped listings
            category: State category (ebay_active, ebay_sold, etc.)
            platform: Platform name for alerts
            listing_type: 'NEW' or 'SOLD'

        Returns:
            List of new listings that were alerted
        """
        new_listings = []
        alerts_sent = 0

        for listing in listings:
            # Get the unique ID
            listing_id = listing.get('item_id') or listing.get('listing_id')

            # Filter: only process listings that match target Pokemon
            title = listing.get('title', '')
            if not self._matches_target_pokemon(title):
                # Still mark as seen to avoid reprocessing, but don't alert
                self.state.mark_seen(category, listing_id)
                continue

            if self.state.is_new(category, listing_id):
                # Mark as seen first (always, for deduplication)
                self.state.mark_seen(category, listing_id)

                # On first run, only alert for first N listings (most recent)
                if self.state.is_first_run:
                    if alerts_sent >= self.FIRST_RUN_ALERT_LIMIT:
                        continue  # Skip alert but still mark as seen

                # This is a new listing!
                logger.info(f"New {listing_type} listing: {listing.get('title', 'Unknown')[:50]}")

                # Send Telegram alert
                success = self.notifier.send_listing_alert(
                    platform=platform,
                    title=listing.get('title', 'Unknown'),
                    price=listing.get('price'),
                    link=listing.get('link', ''),
                    listing_type=listing_type
                )

                if success:
                    logger.info(f"Alert sent for {listing_id}")
                    alerts_sent += 1
                else:
                    logger.warning(f"Failed to send alert for {listing_id}")

                new_listings.append(listing)

        return new_listings


def main():
    """Main entry point."""
    try:
        monitor = ListingMonitor()
        new_listings, sold_listings = monitor.run()

        # Exit with success
        return 0

    except Exception as e:
        logger.error(f"Monitor failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
