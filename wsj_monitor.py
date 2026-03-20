#!/usr/bin/env python3
"""
Manga Scanner — monitors Mercari JP and Yahoo Auctions JP for:
- WSJ first appearance issues (Naruto, Bleach, Yu-Gi-Oh, Dragon Ball, HxH, Romance Dawn, JoJo, One Piece Ch1)
- Vol 1 first editions (Naruto, Bleach, Yu-Gi-Oh, One Piece)
- Other collectible manga (CoroCoro Nov 1996, Comic News 195)

Sends alerts to the manga Telegram bot (separate from the Pokemon no-rarity scanner).
"""

import json
import logging
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from wsj_config import WSJConfig

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

import requests

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(WSJConfig.LOG_FILE, mode='a', encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Telegram notifier (standalone, uses WSJ bot token)
# ---------------------------------------------------------------------------

class WSJTelegramNotifier:
    """Send notifications via the WSJ Telegram bot."""

    def __init__(self):
        self.bot_token = WSJConfig.TELEGRAM_BOT_TOKEN
        self.chat_id = WSJConfig.TELEGRAM_CHAT_ID
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self.bot_token or not self.chat_id:
            logger.warning("WSJ Telegram not configured. Skipping.")
            return False

        url = f"{self.api_base}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False,
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return True
            logger.error(f"Telegram API error: {resp.status_code} - {resp.text}")
            return False
        except requests.RequestException as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    def send_photo(self, photo_url: str, caption: str) -> bool:
        if not self.bot_token or not self.chat_id:
            return False
        url = f"{self.api_base}/sendPhoto"
        payload = {
            "chat_id": self.chat_id,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def send_listing_alert(self, series_name, platform, title, price, link,
                           currency='$', image_url=None):
        """Send a formatted alert for a new WSJ listing."""
        if currency == '¥' and price:
            price_str = f"¥{price:,.0f}" if isinstance(price, (int, float)) else str(price)
        elif price:
            price_str = f"${price:,.2f}" if isinstance(price, (int, float)) else str(price)
        else:
            price_str = "Price not listed"

        message = (
            f"🆕 <b>NEW LISTING [{platform}]</b>\n\n"
            f"📰 <b>{series_name}</b>\n"
            f"📦 {title}\n"
            f"💵 {price_str}\n"
            f"🔗 <a href=\"{link}\">View Listing</a>"
        )

        if image_url:
            return self.send_photo(image_url, message)
        return self.send_message(message)

    def test_connection(self) -> bool:
        url = f"{self.api_base}/getMe"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and resp.json().get("ok"):
                bot_name = resp.json()["result"].get("username", "Unknown")
                logger.info(f"WSJ Telegram bot connected: @{bot_name}")
                return True
            logger.error(f"WSJ Telegram connection failed: {resp.text}")
            return False
        except requests.RequestException as e:
            logger.error(f"WSJ Telegram connection error: {e}")
            return False


# ---------------------------------------------------------------------------
# State manager
# ---------------------------------------------------------------------------

class StateManager:
    """Track seen listings to avoid duplicate alerts."""

    def __init__(self):
        self.state_file = WSJConfig.STATE_FILE
        self.state = self._load()
        self.is_first_run = self.state.get('last_check') is None

    def _load(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load state: {e}")
        return {
            'seen': {},          # listing_id -> first_seen ISO timestamp
            'last_check': None,
            'last_heartbeat': None,
        }

    def save(self):
        self.state['last_check'] = datetime.now().isoformat()
        self._cleanup()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2)

    def _cleanup(self, days=30):
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        self.state['seen'] = {
            k: v for k, v in self.state['seen'].items() if v > cutoff
        }

    def is_new(self, listing_id: str) -> bool:
        if not listing_id:
            return True
        return listing_id not in self.state['seen']

    def mark_seen(self, listing_id: str):
        if listing_id:
            self.state['seen'][listing_id] = datetime.now().isoformat()


# ---------------------------------------------------------------------------
# Browser helpers
# ---------------------------------------------------------------------------

def create_browser_context(playwright):
    browser = playwright.chromium.launch(
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
    return browser, context


def wait_for_page_load(page, timeout_seconds=30):
    for _ in range(timeout_seconds // 5):
        page.wait_for_timeout(5000)
        title = page.title().lower()
        if 'just a moment' not in title and 'checking' not in title:
            return True
    return False


# ---------------------------------------------------------------------------
# Exclusion & relevance filters
# ---------------------------------------------------------------------------

def should_exclude(title: str, exclude_keywords: list[str]) -> bool:
    t = title.lower()
    for kw in exclude_keywords:
        if kw.lower() in t:
            return True
    return False


def _is_reprint(title: str) -> bool:
    """Check if a listing is a reprint/reproduction."""
    t = title.lower()
    t_orig = title
    reprint_keywords = [
        'reprint', 'reproduction', 'replica', 'facsimile', 'reissue',
        '復刻', '復刻版', '復刻盤', 'リプリント', '再版', '再録',
        '愛蔵版', '完全版', '文庫版', '新装版', 'bunko', 'kanzenban',
    ]
    return any(kw in t or kw in t_orig for kw in reprint_keywords)


def is_relevant_listing(title: str, series: dict) -> bool:
    """Check if a listing is the target WSJ issue.

    Requires: correct year + exact issue number + jump/magazine reference, no reprints.
    """
    t = title.lower()
    t_orig = title

    if _is_reprint(title):
        return False

    wsj_year = series.get('wsj_year')
    wsj_number = series.get('wsj_number')

    if not wsj_year or not wsj_number:
        return False

    has_year = wsj_year in t

    # Match exact issue number with word boundaries
    num = wsj_number

    # Handle combined issues like "1・2" (match 1・2, 1-2, 1/2, #1-2, etc.)
    if '・' in num or '-' in num:
        parts = re.split(r'[・\-]', num)
        if len(parts) == 2:
            a, b = parts
            combined_pattern = rf'(?<!\d){a}\s*[・\-/]\s*{b}(?:\s*合併)?'
            has_number = bool(re.search(combined_pattern, t_orig) or re.search(combined_pattern, t))
        else:
            has_number = False
    else:
        has_number = bool(
            re.search(rf'(?<!\d){num}号', t_orig)                        # 43号
            or re.search(rf'#{num}(?!\d)', t)                             # #43
            or re.search(rf'no\.?\s*{num}(?!\d)', t)                      # No.43, No 43
            or re.search(rf'(?:^|[\s#＃])0*{num}(?:[号\s,.\-]|$)', t_orig)  # standalone
        )

    # Must reference jump magazine
    has_jump = any(kw in t or kw in t_orig for kw in [
        'jump', 'wsj', 'ジャンプ',
    ])

    return has_year and has_number and has_jump



# ---------------------------------------------------------------------------
# Mercari Japan scraper (Playwright)
# ---------------------------------------------------------------------------

def search_mercari(page, series_key: str, series: dict) -> list[dict]:
    """Search Mercari JP for a series' WSJ issue and Vol 1."""
    results = []
    seen_ids = set()

    for query in series['mercari_queries']:
        try:
            encoded = quote(query)
            url = f"https://jp.mercari.com/search?keyword={encoded}&order=desc&sort=created_time&status=on_sale"

            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(1500)

            links = page.query_selector_all('a[href*="/item/"]')
            logger.info(f"    Query '{query}': found {len(links)} raw links on page")

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                    item_match = re.search(r'/item/([a-zA-Z0-9]+)', href)
                    if not item_match:
                        continue

                    item_id = item_match.group(1)
                    if item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)

                    text = link.inner_text().strip()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]

                    title_lines = [
                        l for l in lines
                        if not l.startswith('SG') and not l.startswith('US$')
                        and not l.startswith('$') and not l.startswith('¥')
                        and not l.startswith('￥') and not re.match(r'^[\d,\.]+$', l.replace(',', ''))
                        and '¥' not in l and '￥' not in l
                        and not l.startswith('現在')
                        and len(l) > 3
                    ]
                    title = title_lines[0][:120] if title_lines else item_id

                    if should_exclude(title, series['exclude_keywords']):
                        logger.debug(f"    Excluded (keyword): {title[:60]}")
                        continue
                    if not is_relevant_listing(title, series):
                        logger.debug(f"    Excluded (relevance): {title[:60]}")
                        continue

                    logger.info(f"    MATCH: {title[:80]}")
                    price = None
                    price_raw = None
                    for line in lines:
                        m = re.search(r'[¥￥]([\d,]+)', line)
                        if m:
                            try:
                                price_raw = float(m.group(1).replace(',', ''))
                            except ValueError:
                                pass
                            break
                        if re.match(r'^[\d,]+$', line.strip()) and len(line.strip()) >= 3:
                            try:
                                price_raw = float(line.strip().replace(',', ''))
                            except ValueError:
                                pass
                            break

                    full_link = f"https://jp.mercari.com{href}" if not href.startswith('http') else href

                    results.append({
                        'platform': 'Mercari JP',
                        'series': series_key,
                        'title': title,
                        'price': price_raw,
                        'currency': 'JPY',
                        'link': full_link,
                        'listing_id': f"mercari_{item_id}",
                        'image_url': None,
                    })

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Mercari error for '{query}': {e}")

        time.sleep(1)

    # --- Raw Mercari URLs (broader searches with their own filtering) ---
    for raw_url in series.get('mercari_urls', []):
        try:
            page.goto(raw_url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(1500)

            links = page.query_selector_all('a[href*="/item/"]')
            logger.info(f"    Raw URL: found {len(links)} raw links on page")

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                    item_match = re.search(r'/item/([a-zA-Z0-9]+)', href)
                    if not item_match:
                        continue

                    item_id = item_match.group(1)
                    if item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)

                    text = link.inner_text().strip()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]

                    title_lines = [
                        l for l in lines
                        if not l.startswith('SG') and not l.startswith('US$')
                        and not l.startswith('$') and not l.startswith('¥')
                        and not l.startswith('￥') and not re.match(r'^[\d,\.]+$', l.replace(',', ''))
                        and '¥' not in l and '￥' not in l
                        and not l.startswith('現在')
                        and len(l) > 3
                    ]
                    title = title_lines[0][:120] if title_lines else item_id

                    if should_exclude(title, series['exclude_keywords']):
                        logger.debug(f"    Excluded (keyword): {title[:60]}")
                        continue

                    # For raw URLs, use series-specific validation instead of
                    # is_relevant_listing() (which requires year+issue+jump).
                    if not _is_relevant_raw_url_listing(title, series_key):
                        logger.debug(f"    Excluded (raw-url relevance): {title[:60]}")
                        continue

                    logger.info(f"    MATCH (raw URL): {title[:80]}")
                    price_raw = None
                    for line in lines:
                        m = re.search(r'[¥￥]([\d,]+)', line)
                        if m:
                            try:
                                price_raw = float(m.group(1).replace(',', ''))
                            except ValueError:
                                pass
                            break
                        if re.match(r'^[\d,]+$', line.strip()) and len(line.strip()) >= 3:
                            try:
                                price_raw = float(line.strip().replace(',', ''))
                            except ValueError:
                                pass
                            break

                    full_link = f"https://jp.mercari.com{href}" if not href.startswith('http') else href

                    results.append({
                        'platform': 'Mercari JP',
                        'series': series_key,
                        'title': title,
                        'price': price_raw,
                        'currency': 'JPY',
                        'link': full_link,
                        'listing_id': f"mercari_{item_id}",
                        'image_url': None,
                    })

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Mercari raw URL error: {e}")

        time.sleep(1)

    return results


# Spinoff titles to exclude from raw URL results (original series only)
_YUGIOH_SPINOFFS = re.compile(
    r'(?:ファイブディーズ|5D|ゼアル|ZEXAL|アーク・ファイブ|ARC-V|'
    r'セブンス|SEVENS|ゴーラッシュ|GO\s*RUSH|遊戯王R\b|遊戯王ＧＸ|遊戯王GX|'
    r'OCG|デュエルモンスターズカード|VRAINS)',
    re.IGNORECASE,
)


def _is_relevant_raw_url_listing(title: str, series_key: str) -> bool:
    """Relevance check for listings found via raw Mercari URLs.

    These URLs already have keyword + category + price filters baked in,
    so we only need to confirm the title is actually about the target series
    (not a spinoff or unrelated item that Mercari's search matched loosely).
    """
    if _is_reprint(title):
        return False

    if series_key == 'yugioh':
        # Must mention 遊戯王 or 遊☆戯☆王
        if '遊戯王' not in title and '遊☆戯☆王' not in title:
            return False
        # Reject spinoff titles
        if _YUGIOH_SPINOFFS.search(title):
            return False
        return True

    # For other series, fall back to the standard check
    return True


# ---------------------------------------------------------------------------
# Yahoo Auctions Japan scraper (Playwright)
# ---------------------------------------------------------------------------

def _extract_yahoo_listings(page, url: str) -> list[dict]:
    """Extract listings from a Yahoo Auctions search results page.

    Uses a[href*="/jp/auction/"] to match Yahoo's current URL structure
    (items link to /jp/auction/{id}, not /item/{id}).
    """
    listings = []
    seen_ids = set()

    links = page.query_selector_all('a[href*="/jp/auction/"]')
    logger.info(f"    Yahoo page: {len(links)} auction links found")

    if len(links) == 0:
        # Dump page title + snippet for debugging
        try:
            title = page.title()
            snippet = page.inner_text('body')[:300] if page.query_selector('body') else '(no body)'
            logger.warning(f"    Yahoo 0 results — page title: {title}")
            logger.warning(f"    Yahoo page snippet: {snippet[:200]}")
            # Save screenshot for later diagnosis
            debug_path = Path(WSJConfig.DATA_DIR) / 'yahoo_debug.png'
            page.screenshot(path=str(debug_path))
            logger.info(f"    Yahoo debug screenshot saved to {debug_path}")
        except Exception as dbg_err:
            logger.warning(f"    Yahoo debug capture failed: {dbg_err}")

    for link in links:
        try:
            href = link.get_attribute('href')
            if not href:
                continue

            item_match = re.search(r'/jp/auction/([a-zA-Z0-9]+)', href)
            if not item_match:
                continue

            item_id = item_match.group(1)
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            # Parse text content from the link element
            try:
                text = link.inner_text().strip()
            except Exception:
                text = ""

            lines = [l.strip() for l in text.split('\n') if l.strip()]

            # Filter out price/bid/time lines to find the title
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
                and len(l) > 3
            ]
            title = title_lines[0][:120] if title_lines else item_id

            # Extract price (yen)
            price_raw = None
            for line in lines:
                yen_match = re.search(r'(?:現在|即決)?[¥￥]?([\d,]+)円?', line)
                if yen_match and ('円' in line or '¥' in line or '￥' in line
                                  or line.startswith('現在') or line.startswith('即決')):
                    try:
                        price_raw = float(yen_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
                    break
                elif re.match(r'^[\d,]+$', line):
                    try:
                        price_raw = float(line.replace(',', ''))
                    except ValueError:
                        pass
                    break

            full_link = href if href.startswith('http') else f"https://auctions.yahoo.co.jp{href}"
            listing_id = f"yahoo_{item_id}"

            listings.append({
                'item_id': item_id,
                'listing_id': listing_id,
                'title': title,
                'price': price_raw,
                'currency': 'JPY',
                'link': full_link,
                'image_url': None,
            })

        except Exception:
            continue

    return listings


def _wait_for_yahoo_page(page):
    """Wait for Yahoo Auctions page to load, handling bot challenges."""
    # Yahoo sometimes shows interstitial challenges — wait longer than Mercari
    for _ in range(6):
        page.wait_for_timeout(3000)
        title = page.title().lower()
        if 'just a moment' not in title and 'checking' not in title and 'verify' not in title:
            return True
    logger.warning("    Yahoo page may be stuck on a challenge page")
    return False


def search_yahoo_auctions(page, series_key: str, series: dict) -> list[dict]:
    """Search Yahoo Auctions JP for a series' WSJ issue and Vol 1."""
    results = []
    seen_titles = set()

    for query in series['yahoo_queries']:
        try:
            encoded = quote(query)
            url = f"https://auctions.yahoo.co.jp/search/search?p={encoded}&va={encoded}&exflg=1&b=1&n=50"

            page.goto(url, timeout=60000)
            _wait_for_yahoo_page(page)

            raw_listings = _extract_yahoo_listings(page, url)
            logger.info(f"    Query '{query}': {len(raw_listings)} listings extracted")

            for listing in raw_listings:
                title = listing['title']

                if should_exclude(title, series['exclude_keywords']):
                    continue
                if not is_relevant_listing(title, series):
                    continue

                title_key = title[:50]
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                results.append({
                    'platform': 'Yahoo Auctions JP',
                    'series': series_key,
                    'title': title,
                    'price': listing['price'],
                    'currency': 'JPY',
                    'link': listing['link'],
                    'listing_id': listing['listing_id'],
                    'image_url': listing['image_url'],
                })

        except Exception as e:
            logger.error(f"Yahoo error for '{query}': {e}")

        time.sleep(1)

    return results


# ---------------------------------------------------------------------------
# Main monitor
# ---------------------------------------------------------------------------

class WSJMonitor:
    """Main WSJ manga monitor orchestrator."""

    FIRST_RUN_ALERT_LIMIT = 10  # Max alerts per series on first run

    def __init__(self):
        self.state = StateManager()
        self.notifier = WSJTelegramNotifier()

    def _should_send_heartbeat(self) -> bool:
        last = self.state.state.get('last_heartbeat')
        if not last:
            return True
        try:
            hours_since = (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 3600
            return hours_since >= 24
        except (ValueError, TypeError):
            return True

    def _send_heartbeat(self):
        if not self._should_send_heartbeat():
            return
        series_list = ', '.join(s['name'] for s in WSJConfig.SERIES.values())
        simple_list = ', '.join(s['name'] for s in WSJConfig.SIMPLE_SEARCHES)
        unfiltered_list = ', '.join(s['name'] for s in WSJConfig.UNFILTERED_MERCARI_URLS)
        msg = (
            "💚 <b>Manga Scanner Active</b>\n\n"
            f"Daily check-in at {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"WSJ Issues: {series_list}\n"
            f"Other: {simple_list}\n"
        )
        if unfiltered_list:
            msg += f"Unfiltered: {unfiltered_list}\n"
        msg += "Platforms: Mercari JP, Yahoo Auctions JP"
        if self.notifier.send_message(msg):
            self.state.state['last_heartbeat'] = datetime.now().isoformat()
            logger.info("Heartbeat sent")

    def _validate_simple(self, title: str, validators: list[list[str]]) -> bool:
        """Check title against AND/OR validators (for SIMPLE_SEARCHES)."""
        if not title:
            return False
        t = title.lower()

        # Check global exclude
        for kw in WSJConfig.GLOBAL_EXCLUDE:
            if kw.lower() in t:
                return False

        return all(
            any(alt.lower() in t for alt in alternatives)
            for alternatives in validators
        )

    def _process_results(self, all_results: list[dict]) -> int:
        """Process results, send alerts for new listings. Returns alert count."""
        alerts_sent = 0
        alerts_per_series = {}

        for result in all_results:
            listing_id = result['listing_id']
            series_key = result['series']
            series = WSJConfig.SERIES.get(series_key)

            if not self.state.is_new(listing_id):
                self.state.mark_seen(listing_id)
                continue

            self.state.mark_seen(listing_id)

            # First run throttle per series
            if self.state.is_first_run:
                count = alerts_per_series.get(series_key, 0)
                if count >= self.FIRST_RUN_ALERT_LIMIT:
                    continue
                alerts_per_series[series_key] = count + 1

            title = result['title']
            currency = '¥' if result['currency'] == 'JPY' else '$'

            # series_name from WSJ_SERIES or from simple search result
            display_name = result.get('series_name') or (series['name'] if series else series_key)

            success = self.notifier.send_listing_alert(
                series_name=display_name,
                platform=result['platform'],
                title=title,
                price=result['price'],
                link=result['link'],
                currency=currency,
                image_url=result.get('image_url'),
            )

            if success:
                alerts_sent += 1
                safe_title = title.encode('ascii', 'replace').decode('ascii')[:50]
                logger.info(f"Alert sent: [{result['platform']}] {safe_title}")
            else:
                logger.warning(f"Alert failed for {listing_id}")

            # Rate limit Telegram
            time.sleep(0.5)

        return alerts_sent

    def run(self):
        """Run the full monitoring cycle."""
        logger.info("=" * 60)
        logger.info(f"Manga Scanner run at {datetime.now()}")

        missing = WSJConfig.validate()
        if missing:
            logger.warning(f"Missing config: {', '.join(missing)}")
            logger.warning("Telegram alerts disabled.")

        self._send_heartbeat()

        if self.state.is_first_run:
            logger.info("First run - will limit alerts to most recent listings")
            series_lines = '\n'.join(
                f"• {s['name']} ({s['wsj_issue']})" for s in WSJConfig.SERIES.values() if s.get('wsj_issue')
            )
            self.notifier.send_message(
                f"🔄 <b>WSJ Monitor Started</b>\n\n"
                f"Watching for WSJ first appearances:\n{series_lines}\n\n"
                f"Platforms: Mercari JP, Yahoo Auctions JP"
            )

        all_results = []

        # --- Japanese marketplaces (shared Playwright browser) ---
        if PLAYWRIGHT_AVAILABLE:
            try:
                with sync_playwright() as p:
                    browser, context = create_browser_context(p)
                    page = context.new_page()

                    for series_key, series in WSJConfig.SERIES.items():
                        # Mercari JP
                        logger.info(f"Mercari JP search: {series['name']}")
                        try:
                            mercari_results = search_mercari(page, series_key, series)
                            all_results.extend(mercari_results)
                            logger.info(f"  Mercari {series['name']}: {len(mercari_results)} results")
                        except Exception as e:
                            logger.error(f"  Mercari {series['name']} failed: {e}")

                        # Yahoo Auctions JP
                        logger.info(f"Yahoo Auctions search: {series['name']}")
                        try:
                            yahoo_results = search_yahoo_auctions(page, series_key, series)
                            all_results.extend(yahoo_results)
                            logger.info(f"  Yahoo {series['name']}: {len(yahoo_results)} results")
                        except Exception as e:
                            logger.error(f"  Yahoo {series['name']} failed: {e}")

                    # --- Simple searches (Vol 1, CoroCoro, Comic News, etc.) ---
                    for search in WSJConfig.SIMPLE_SEARCHES:
                        sname = search['name']
                        logger.info(f"Simple search: {sname}")

                        # Mercari keyword search (use mercari_url if provided, else build from keyword)
                        mercari_url = search.get('mercari_url')
                        mercari_kw = search.get('mercari_keyword')
                        if mercari_url or mercari_kw:
                            try:
                                url = mercari_url or f"https://jp.mercari.com/search?keyword={quote(mercari_kw)}&order=desc&sort=created_time&status=on_sale"
                                page.goto(url, timeout=60000)
                                wait_for_page_load(page)
                                page.wait_for_timeout(1500)

                                links = page.query_selector_all('a[href*="/item/"]')
                                logger.info(f"  Mercari '{sname}': {len(links)} raw links")

                                for link in links:
                                    try:
                                        href = link.get_attribute('href')
                                        if not href:
                                            continue
                                        item_match = re.search(r'/item/([a-zA-Z0-9]+)', href)
                                        if not item_match:
                                            continue
                                        item_id = item_match.group(1)

                                        text = link.inner_text().strip()
                                        lines = [l.strip() for l in text.split('\n') if l.strip()]
                                        title_lines = [
                                            l for l in lines
                                            if not l.startswith('SG') and not l.startswith('US$')
                                            and not l.startswith('$') and not l.startswith('¥')
                                            and not l.startswith('￥') and not re.match(r'^[\d,\.]+$', l.replace(',', ''))
                                            and '¥' not in l and '￥' not in l
                                            and not l.startswith('現在')
                                            and len(l) > 3
                                        ]
                                        title = title_lines[0][:120] if title_lines else item_id

                                        if not self._validate_simple(title, search['validators']):
                                            continue

                                        price_raw = None
                                        for line in lines:
                                            m = re.search(r'[¥￥]([\d,]+)', line)
                                            if m:
                                                try:
                                                    price_raw = float(m.group(1).replace(',', ''))
                                                except ValueError:
                                                    pass
                                                break

                                        full_link = f"https://jp.mercari.com{href}" if not href.startswith('http') else href
                                        all_results.append({
                                            'platform': 'Mercari JP',
                                            'series': search['state_category'],
                                            'series_name': sname,
                                            'title': title,
                                            'price': price_raw,
                                            'currency': 'JPY',
                                            'link': full_link,
                                            'listing_id': f"mercari_{item_id}",
                                            'image_url': None,
                                        })
                                    except Exception:
                                        continue
                            except Exception as e:
                                logger.error(f"  Mercari simple search error for '{sname}': {e}")
                            time.sleep(1)

                        # Yahoo Auctions keyword search
                        yahoo_kw = search.get('yahoo_keyword')
                        if yahoo_kw:
                            try:
                                encoded = quote(yahoo_kw)
                                url = f"https://auctions.yahoo.co.jp/search/search?p={encoded}&va={encoded}&exflg=1&b=1&n=50"
                                page.goto(url, timeout=60000)
                                _wait_for_yahoo_page(page)

                                raw_listings = _extract_yahoo_listings(page, url)
                                logger.info(f"  Yahoo '{sname}': {len(raw_listings)} listings extracted")

                                for listing in raw_listings:
                                    title = listing['title']

                                    if not self._validate_simple(title, search['validators']):
                                        continue

                                    all_results.append({
                                        'platform': 'Yahoo Auctions JP',
                                        'series': search['state_category'],
                                        'series_name': sname,
                                        'title': title,
                                        'price': listing['price'],
                                        'currency': 'JPY',
                                        'link': listing['link'],
                                        'listing_id': listing['listing_id'],
                                        'image_url': listing['image_url'],
                                    })
                            except Exception as e:
                                logger.error(f"  Yahoo simple search error for '{sname}': {e}")
                            time.sleep(1)

                    # --- Unfiltered Mercari URL searches (no filtering, alert on everything) ---
                    for search in WSJConfig.UNFILTERED_MERCARI_URLS:
                        sname = search['name']
                        logger.info(f"Unfiltered Mercari search: {sname}")
                        try:
                            page.goto(search['url'], timeout=60000)
                            wait_for_page_load(page)
                            page.wait_for_timeout(1500)

                            links = page.query_selector_all('a[href*="/item/"]')
                            logger.info(f"  Unfiltered '{sname}': {len(links)} raw links")

                            seen_ids = set()
                            for link in links:
                                try:
                                    href = link.get_attribute('href')
                                    if not href:
                                        continue
                                    item_match = re.search(r'/item/([a-zA-Z0-9]+)', href)
                                    if not item_match:
                                        continue
                                    item_id = item_match.group(1)
                                    if item_id in seen_ids:
                                        continue
                                    seen_ids.add(item_id)

                                    text = link.inner_text().strip()
                                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                                    title_lines = [
                                        l for l in lines
                                        if not l.startswith('SG') and not l.startswith('US$')
                                        and not l.startswith('$') and not l.startswith('¥')
                                        and not l.startswith('￥') and not re.match(r'^[\d,\.]+$', l.replace(',', ''))
                                        and '¥' not in l and '￥' not in l
                                        and not l.startswith('現在')
                                        and len(l) > 3
                                    ]
                                    title = title_lines[0][:120] if title_lines else item_id

                                    price_raw = None
                                    for line in lines:
                                        m = re.search(r'[¥￥]([\d,]+)', line)
                                        if m:
                                            try:
                                                price_raw = float(m.group(1).replace(',', ''))
                                            except ValueError:
                                                pass
                                            break
                                        if re.match(r'^[\d,]+$', line.strip()) and len(line.strip()) >= 3:
                                            try:
                                                price_raw = float(line.strip().replace(',', ''))
                                            except ValueError:
                                                pass
                                            break

                                    full_link = f"https://jp.mercari.com{href}" if not href.startswith('http') else href
                                    all_results.append({
                                        'platform': 'Mercari JP',
                                        'series': search['state_category'],
                                        'series_name': sname,
                                        'title': title,
                                        'price': price_raw,
                                        'currency': 'JPY',
                                        'link': full_link,
                                        'listing_id': f"mercari_{item_id}",
                                        'image_url': None,
                                    })
                                except Exception:
                                    continue
                        except Exception as e:
                            logger.error(f"  Unfiltered Mercari search error for '{sname}': {e}")
                        time.sleep(1)

                    browser.close()
            except Exception as e:
                logger.error(f"Playwright session failed: {e}")
                self.notifier.send_message(f"⚠️ <b>Manga Scanner Error</b>\n\nPlaywright: {str(e)[:200]}")
        else:
            logger.warning("Playwright not available - skipping Mercari JP and Yahoo Auctions JP")

        # --- Process & alert ---
        logger.info(f"Total results across all platforms: {len(all_results)}")
        alerts_sent = self._process_results(all_results)

        # Save state
        self.state.save()

        logger.info(f"Run complete. {len(all_results)} results, {alerts_sent} new alerts sent.")
        logger.info("=" * 60)

        return all_results, alerts_sent


def main():
    try:
        monitor = WSJMonitor()
        results, alerts = monitor.run()
        return 0
    except Exception as e:
        logger.error(f"WSJ Monitor failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
