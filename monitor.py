#!/usr/bin/env python3
"""
Listing Monitor for Mercari Japan and eBay.
Checks specific searches and sends Telegram alerts for new validated listings.

Run via cron every 15 minutes:
*/15 * * * * cd /path/to/pokeanalysis && python3 monitor.py >> /var/log/pokeanalysis.log 2>&1
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from config import Config
from scraper import EbayScraper
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

        state = {
            'last_check': None,
            'last_heartbeat': None,
        }
        # Add state categories for each monitored search
        for search in Config.MONITORED_SEARCHES:
            state[search['state_category']] = {}
        return state

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

        for search in Config.MONITORED_SEARCHES:
            category = search['state_category']
            if category in self.state and isinstance(self.state[category], dict):
                self.state[category] = {
                    k: v for k, v in self.state[category].items()
                    if v > cutoff_str
                }

    def is_new(self, category: str, listing_id: str) -> bool:
        """Check if a listing is new (not seen before)."""
        if not listing_id:
            return True
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

    FIRST_RUN_ALERT_LIMIT = 20

    def __init__(self):
        self.state = StateManager()
        self.notifier = TelegramNotifier()
        self.wsj_notifier = TelegramNotifier(
            bot_token=Config.WSJ_TELEGRAM_BOT_TOKEN,
            chat_id=Config.WSJ_TELEGRAM_CHAT_ID,
        )
        self.ebay_scraper = EbayScraper()
        self.mercari_scraper = MercariScraper()

    def _validate_listing(self, title: str, validators: list[list[str]], exclude: list[str] = None) -> bool:
        """Check title against validation rules.

        Each validator is a list of alternatives (OR).
        All validators must pass (AND).
        If any exclude term is found, the listing is rejected.
        """
        if not title:
            return False
        title_lower = title.lower()

        # Reject if any exclude term found
        all_exclude = list(Config.GLOBAL_EXCLUDE) + (exclude or [])
        if any(term.lower() in title_lower for term in all_exclude):
            return False

        return all(
            any(alt.lower() in title_lower for alt in alternatives)
            for alternatives in validators
        )

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

        search_names = ', '.join(s['name'] for s in Config.MONITORED_SEARCHES)
        message = (
            "💚 <b>Monitor Active</b>\n\n"
            f"Daily check-in at {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"Watching: {search_names}"
        )

        if self.notifier.send_message(message):
            self.state.state['last_heartbeat'] = datetime.now().isoformat()
            logger.info("Daily heartbeat sent")

    def run(self):
        """Run the full monitoring cycle."""
        logger.info("=" * 50)
        logger.info(f"Starting monitor run at {datetime.now()}")

        # Validate configuration
        missing = Config.validate()
        if missing:
            logger.warning(f"Missing configuration: {', '.join(missing)}")
            logger.warning("Telegram notifications will be disabled.")

        # Send daily heartbeat
        self._send_heartbeat()

        # First run notification
        if self.state.is_first_run:
            logger.info("First run detected - will send alerts for most recent listings only")
            self.notifier.send_message(
                "🔄 <b>Monitor Started</b>\n\n"
                "Sending alerts for recent listings.\n"
                "Future runs will only alert on NEW listings."
            )

        all_new = []

        try:
            for search in Config.MONITORED_SEARCHES:
                name = search['name']
                platform = search['platform']
                keyword = search['keyword']
                category = search['state_category']
                validators = search['validators']

                safe_name = name.encode('ascii', 'replace').decode('ascii')
                logger.info(f"Checking: {safe_name} ({platform})...")

                # Scrape listings
                listings = []
                if platform == 'mercari':
                    listings = self.mercari_scraper.search_listings(keyword=keyword)
                elif platform == 'ebay':
                    listings = self.ebay_scraper.scrape_active_listings(keyword, max_pages=1)

                logger.info(f"  Found {len(listings)} raw listings")

                # Process: validate, dedup, alert
                alerts_sent = 0
                for listing in listings:
                    listing_id = listing.get('item_id') or listing.get('listing_id')
                    title = listing.get('title', '')

                    # Validate title matches expected content
                    if not self._validate_listing(title, validators, search.get('exclude')):
                        self.state.mark_seen(category, listing_id)
                        continue

                    if not self.state.is_new(category, listing_id):
                        continue

                    # Mark as seen
                    self.state.mark_seen(category, listing_id)

                    # On first run, limit alerts
                    if self.state.is_first_run and alerts_sent >= self.FIRST_RUN_ALERT_LIMIT:
                        continue

                    safe_title = title.encode('ascii', 'replace').decode('ascii')[:60]
                    logger.info(f"  New listing: {safe_title}")

                    # Send alert - pick the right bot
                    is_mercari = platform == 'mercari'
                    currency = '¥' if is_mercari else '$'
                    platform_label = f"Mercari ({name})" if is_mercari else f"eBay ({name})"
                    notifier = self.wsj_notifier if search.get('bot') == 'wsj' else self.notifier

                    success = notifier.send_listing_alert(
                        platform=platform_label,
                        title=title,
                        price=listing.get('price'),
                        link=listing.get('link', ''),
                        listing_type='NEW',
                        currency=currency,
                        image_url=listing.get('image_url')
                    )

                    if success:
                        alerts_sent += 1
                        logger.info(f"  Alert sent for {listing_id}")
                    else:
                        logger.warning(f"  Failed to send alert for {listing_id}")

                    all_new.append(listing)

                logger.info(f"  {alerts_sent} new alerts sent for {safe_name}")

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            self.notifier.send_error(f"Scraping error: {str(e)[:200]}")

        # Save updated state
        self.state.save_state()

        logger.info(f"Run complete. Total new alerts: {len(all_new)}")
        logger.info("=" * 50)

        return all_new


def main():
    """Main entry point."""
    try:
        monitor = ListingMonitor()
        new_listings = monitor.run()
        return 0
    except Exception as e:
        logger.error(f"Monitor failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
