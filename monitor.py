#!/usr/bin/env python3
"""
No-Rarity Scanner — monitors Mercari Japan and eBay for Pokemon game cartridges.
Sends alerts to the main Telegram bot.
"""

import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from config import Config
from mercari_scraper import MercariScraper, PLAYWRIGHT_AVAILABLE as MERCARI_PLAYWRIGHT
from yahoo_auctions_scraper import YahooAuctionsScraper
from scraper import EbayScraper
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

        logger.debug(f"State saved to {self.state_file}")

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
    # Stop starting new scrapes after this long, so results are always
    # processed and state is saved before the workflow's 50-minute kill.
    SCRAPE_BUDGET_S = 38 * 60
    # A crashing browser is relaunched, but not forever.
    MERCARI_MAX_RELAUNCHES = 5

    def __init__(self):
        self.state = StateManager()
        self.notifier = TelegramNotifier()
        self.mercari_scraper = MercariScraper()
        self.yahoo_scraper = YahooAuctionsScraper()
        self.ebay_scraper = EbayScraper()

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

        # Conditional requirements: a title matching a trigger must also carry
        # one of the required terms (e.g. 体験版 is only wanted when 未開封).
        # An optional third element lists exemptions that switch the rule off.
        for rule in getattr(Config, 'CONDITIONAL_REQUIRE', []):
            triggers, required = rule[0], rule[1]
            exempt = rule[2] if len(rule) > 2 else []
            if not any(t.lower() in title_lower for t in triggers):
                continue
            if any(e.lower() in title_lower for e in exempt):
                continue
            if not any(r.lower() in title_lower for r in required):
                return False

        return all(
            any(alt.lower() in title_lower for alt in alternatives)
            for alternatives in validators
        )

    def _scrape_all(self) -> dict:
        """Scrape every (platform, keyword) once, the platforms in parallel.

        Returns {(platform, keyword): listings}. A keyword that failed or ran
        past the time budget is absent from the result (not an empty list),
        so it can't be mistaken for "no listings".
        """
        jobs: dict[str, list[str]] = {}
        for search in Config.MONITORED_SEARCHES:
            if not search.get('enabled', True):
                continue
            kws = jobs.setdefault(search['platform'], [])
            for kw in search.get('keywords') or [search['keyword']]:
                if kw not in kws:
                    kws.append(kw)

        deadline = time.monotonic() + self.SCRAPE_BUDGET_S
        workers = {
            'mercari': lambda kws: self._scrape_mercari(kws, deadline),
            'yahoo': lambda kws: self._scrape_each(
                'yahoo', kws, deadline,
                lambda kw: self.yahoo_scraper.search_listings(keyword=kw)),
            'ebay': lambda kws: self._scrape_each(
                'ebay', kws, deadline,
                lambda kw: self.ebay_scraper.scrape_active_listings(search_term=kw, max_pages=1)),
        }
        for platform in jobs:
            if platform not in workers:
                logger.warning(f"Unknown platform '{platform}' - its searches are skipped")

        results = {}
        with ThreadPoolExecutor(max_workers=len(workers)) as executor:
            futures = {
                executor.submit(self._timed, platform, fn, jobs[platform]): platform
                for platform, fn in workers.items() if jobs.get(platform)
            }
            for future in as_completed(futures):
                try:
                    results.update(future.result())
                except Exception as e:
                    logger.error(f"{futures[future]} scraping failed: {e}")
        return results

    @staticmethod
    def _timed(platform, fn, keywords) -> dict:
        start = time.monotonic()
        out = fn(keywords)
        logger.info(f"[{platform}] scraped {len(out)}/{len(keywords)} keywords "
                    f"in {(time.monotonic() - start) / 60:.1f} min")
        return out

    @staticmethod
    def _scrape_each(platform, keywords, deadline, fetch) -> dict:
        """Scrape keywords one at a time with a stateless fetch function."""
        out = {}
        for i, kw in enumerate(keywords):
            if time.monotonic() >= deadline:
                logger.warning(f"[{platform}] time budget reached - "
                               f"{len(keywords) - i} keywords not scraped")
                break
            try:
                out[(platform, kw)] = fetch(kw)
            except Exception as e:
                logger.warning(f"[{platform}] search failed: {e}")
        return out

    def _scrape_mercari(self, keywords, deadline) -> dict:
        """Scrape all Mercari keywords in one browser, relaunching on a crash."""
        if not MERCARI_PLAYWRIGHT:
            logger.warning("[mercari] Playwright not installed - Mercari skipped")
            return {}
        out = {}
        pending = list(keywords)
        relaunches = 0
        while pending and time.monotonic() < deadline:
            try:
                with self.mercari_scraper.session() as session:
                    while pending and time.monotonic() < deadline:
                        out[('mercari', pending[0])] = session.search(keyword=pending[0])
                        pending.pop(0)
            except Exception as e:
                # Drop the keyword that was in flight so a page that reliably
                # breaks the browser can't stall the rest. (Nothing is in
                # flight if the error came from closing the browser at the end.)
                if pending:
                    pending.pop(0)
                relaunches += 1
                logger.warning(f"[mercari] browser failed ({e}); "
                               f"relaunch {relaunches}/{self.MERCARI_MAX_RELAUNCHES}")
                if relaunches >= self.MERCARI_MAX_RELAUNCHES:
                    break
        if pending:
            logger.warning(f"[mercari] {len(pending)} keywords not scraped")
        return out

    def run(self):
        """Run the full monitoring cycle."""
        logger.info("=" * 50)
        logger.info(f"Starting monitor run at {datetime.now()}")

        # Validate configuration
        missing = Config.validate()
        if missing:
            logger.warning(f"Missing configuration: {', '.join(missing)}")
            logger.warning("Telegram notifications will be disabled.")

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
            # Scrape everything first (platforms in parallel), then validate
            # and alert in search order on this thread — the state and the
            # notifier are only ever touched here.
            scrape_start = time.monotonic()
            scraped = self._scrape_all()
            logger.info(f"Scraping finished in {(time.monotonic() - scrape_start) / 60:.1f} min")

            for search in Config.MONITORED_SEARCHES:
                name = search['name']
                platform = search['platform']
                # A search may carry a single 'keyword' or a list of 'keywords'.
                keywords = search.get('keywords') or [search['keyword']]
                category = search['state_category']
                validators = search['validators']

                safe_name = name.encode('ascii', 'replace').decode('ascii')

                # Allow temporarily disabling a search without deleting it.
                if not search.get('enabled', True):
                    logger.info(f"Skipping (disabled): {safe_name} ({platform})")
                    continue

                logger.info(f"Checking: {safe_name} ({platform})...")

                # Combine this search's keyword results + dedup.
                listings = []
                seen_scrape = set()
                scraped_keywords = 0
                for kw in keywords:
                    batch = scraped.get((platform, kw))
                    if batch is None:
                        continue
                    scraped_keywords += 1
                    for l in batch:
                        lid = l.get('item_id') or l.get('listing_id')
                        if lid and lid in seen_scrape:
                            continue
                        if lid:
                            seen_scrape.add(lid)
                        listings.append(l)

                if not scraped_keywords:
                    logger.warning(f"  Not scraped this run (error or time budget): {safe_name}")
                    continue
                logger.info(f"  Found {len(listings)} raw listings"
                            f" ({scraped_keywords}/{len(keywords)} keywords)")

                # Process: validate, dedup, alert
                alerts_sent = 0
                for listing in listings:
                    listing_id = listing.get('item_id') or listing.get('listing_id')
                    title = listing.get('title', '')

                    # Validate title matches expected content
                    if not self._validate_listing(title, validators, search.get('exclude')):
                        self.state.mark_seen(category, listing_id)
                        continue

                    # eBay only: keep Japanese-version listings (Mercari/Yahoo
                    # are already Japanese). Require a JP marker, reject other
                    # regions (PAL/US/EU/etc).
                    if platform == 'ebay':
                        tl = title.lower()
                        if any(r in tl for r in Config.EBAY_REGION_EXCLUDE) or \
                           not any(m.lower() in tl for m in Config.EBAY_JP_MARKERS):
                            self.state.mark_seen(category, listing_id)
                            continue

                    if not self.state.is_new(category, listing_id):
                        continue

                    # On first run, mark as baseline (seen) and limit alerts so we
                    # don't blast the entire pre-existing inventory.
                    if self.state.is_first_run and alerts_sent >= self.FIRST_RUN_ALERT_LIMIT:
                        self.state.mark_seen(category, listing_id)
                        continue

                    safe_title = title.encode('ascii', 'replace').decode('ascii')[:60]
                    logger.info(f"  New listing: {safe_title}")

                    # Send alert
                    if platform == 'ebay':
                        currency = listing.get('currency', '$')
                        platform_label = f"eBay ({name})"
                    elif platform == 'yahoo':
                        currency = listing.get('currency', '¥')
                        platform_label = f"Yahoo ({name})"
                    else:
                        currency = listing.get('currency', '¥')
                        platform_label = f"Mercari ({name})"

                    success = self.notifier.send_listing_alert(
                        platform=platform_label,
                        title=title,
                        price=listing.get('price'),
                        link=listing.get('link', ''),
                        listing_type='NEW',
                        currency=currency,
                        image_url=listing.get('image_url')
                    )

                    if success:
                        # Only mark seen after a confirmed send, so a failed
                        # send is retried next run instead of silently swallowed.
                        self.state.mark_seen(category, listing_id)
                        alerts_sent += 1
                        all_new.append(listing)
                        logger.info(f"  Alert sent for {listing_id}")
                        # Persist immediately. A full pass takes ~33 min and the
                        # GHA job cap kills it mid-run; without this, every alert
                        # already sent replays on the next run (the FF5 Famicom
                        # listing fired every ~30 min for hours).
                        self.state.save_state()
                    else:
                        logger.warning(f"  Failed to send alert for {listing_id} (will retry next run)")

                logger.info(f"  {alerts_sent} new alerts sent for {safe_name}")

                # Checkpoint after every search so a killed run keeps the
                # baseline it built, not just the alerts it sent.
                self.state.save_state()

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
