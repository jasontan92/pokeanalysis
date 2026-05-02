"""
Ad-hoc search for Weekly Shonen Champion 1991 #43 - Grappler Baki debut.
週刊少年チャンピオン 1991年 43号 板垣恵介 グラップラー刃牙 連載開始

This is the issue containing the debut/serialization start of Itagaki Keisuke's
"Grappler Baki" (グラップラー刃牙).
Published September 30, 1991 by Akita Shoten (秋田書店).

Platforms: eBay, Fanatics Collect, Mercari JP, Yahoo Auctions JP, Magi,
           SNKRDUNK, Mandarake, Surugaya, Rakuma
Live listings only.
"""

import re
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, quote_plus

# Fix Windows console encoding for Japanese characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: Playwright not installed.")


# ---------------------------------------------------------------------------
# Search queries per platform — VERY broad net for a rare issue
# ---------------------------------------------------------------------------

# eBay (English + Japanese) — cast the widest net
EBAY_QUERIES = [
    # Exact issue
    "weekly shonen champion 1991 43",
    "weekly shonen champion 1991 #43",
    "shonen champion 1991 #43",
    "shonen champion 1991 no 43",
    "shonen champion 1991 no. 43",
    "wsc 1991 43",
    # Grappler Baki specific
    "shonen champion grappler baki 1991",
    "grappler baki debut shonen champion",
    "grappler baki first issue champion 1991",
    "grappler baki weekly champion 1991",
    "grappler baki magazine debut",
    "grappler baki chapter 1 magazine",
    "baki 1991 champion debut",
    # Japanese on eBay
    "週刊少年チャンピオン 1991 43",
    "週刊少年チャンピオン 1991年 43号",
    "少年チャンピオン 1991 43号",
    "グラップラー刃牙 週刊少年チャンピオン 1991",
    "グラップラー刃牙 連載開始 チャンピオン",
    "刃牙 チャンピオン 1991",
    # Graded
    "shonen champion 1991 43 cgc",
    "shonen champion 1991 43 bgs",
    "weekly shonen champion 1991 43 graded",
    "grappler baki champion cgc",
    "grappler baki champion bgs",
    # Itagaki / debut
    "itagaki keisuke first shonen champion 1991",
    "板垣恵介 チャンピオン 1991",
    # Broad fallbacks
    "weekly shonen champion 1991 september",
    "shonen champion 1991 itagaki",
]

# Fanatics Collect (English)
FANATICS_QUERIES = [
    "shonen champion 1991 43",
    "weekly shonen champion 1991 43",
    "grappler baki shonen champion",
    "grappler baki champion 1991",
    "shonen champion grappler baki",
    "baki debut shonen champion",
]

# SNKRDUNK (Japanese)
SNKRDUNK_QUERIES = [
    "週刊少年チャンピオン 1991 43",
    "少年チャンピオン 1991年43号",
    "グラップラー刃牙 チャンピオン",
    "刃牙 少年チャンピオン",
    "チャンピオン 1991 43号",
    "板垣恵介 チャンピオン 1991",
]

# Magi (Japanese collectibles)
MAGI_QUERIES = [
    "週刊少年チャンピオン 1991 43",
    "週刊少年チャンピオン 1991年43号",
    "少年チャンピオン 1991年43号",
    "グラップラー刃牙 チャンピオン 1991",
    "グラップラー刃牙 連載開始 チャンピオン",
    "板垣恵介 チャンピオン 1991",
    "チャンピオン 1991 43号",
    "週刊少年チャンピオン 1991 43号 板垣",
    "グラップラー刃牙 新連載 チャンピオン",
    "刃牙 連載開始 1991",
]

# Mercari Japan — maximum coverage
MERCARI_QUERIES = [
    # Exact issue number
    "週刊少年チャンピオン 1991年43号",
    "週刊少年チャンピオン 1991 43号",
    "少年チャンピオン 1991年43号",
    "少年チャンピオン 1991 43号",
    "チャンピオン 1991年 43号",
    "チャンピオン 1991 43号",
    # Grappler Baki
    "グラップラー刃牙 チャンピオン 1991",
    "グラップラー刃牙 週刊少年チャンピオン",
    "グラップラー刃牙 連載開始",
    "グラップラー刃牙 新連載",
    "グラップラー刃牙 第1話 チャンピオン",
    "刃牙 チャンピオン 1991",
    "刃牙 少年チャンピオン 1991",
    # Itagaki Keisuke
    "板垣恵介 チャンピオン 1991 43",
    "板垣恵介 少年チャンピオン 1991",
    "板垣恵介 グラップラー刃牙",
    # Graded
    "週刊少年チャンピオン 1991年43号 鑑定",
    "グラップラー刃牙 チャンピオン CGC",
    # Broader
    "週刊少年チャンピオン 1991 43",
    "少年チャンピオン 1991年 43",
    # Batch/lot that might include #43
    "週刊少年チャンピオン 1991年 まとめ",
    "少年チャンピオン 1991 まとめ",
]

# Yahoo Auctions Japan — heavy coverage
YAHOO_QUERIES = [
    "週刊少年チャンピオン 1991年 43号",
    "週刊少年チャンピオン 1991 43号",
    "週刊少年チャンピオン 1991 43",
    "少年チャンピオン 1991年43号",
    "少年チャンピオン 1991 43号",
    "チャンピオン 1991年 43号",
    "チャンピオン 1991 43号",
    "グラップラー刃牙 チャンピオン 1991",
    "刃牙 少年チャンピオン 1991",
    "板垣恵介 チャンピオン 1991",
    "板垣恵介 少年チャンピオン 1991",
    "週刊少年チャンピオン 1991年43号 板垣",
    "グラップラー刃牙 連載開始 チャンピオン",
    "週刊少年チャンピオン 1991 43 グラップラー",
    # Broader 1991 champion searches
    "週刊少年チャンピオン 1991年 9月",
    "少年チャンピオン 1991 まとめ",
    "weekly shonen champion 1991 43",
]

# Mandarake (Japanese collectibles store)
MANDARAKE_QUERIES = [
    "週刊少年チャンピオン 1991年 43号",
    "週刊少年チャンピオン 1991 43",
    "少年チャンピオン 1991 43",
    "グラップラー刃牙 チャンピオン",
    "刃牙 チャンピオン",
    "少年チャンピオン グラップラー刃牙 1991",
    "週刊少年チャンピオン 1991年43号",
    "板垣恵介 チャンピオン 1991",
    "週刊少年チャンピオン 1991",
    "グラップラー刃牙 新連載 チャンピオン",
]

# Surugaya (Japanese used goods)
SURUGAYA_QUERIES = [
    "週刊少年チャンピオン 1991年 43号",
    "少年チャンピオン 1991 43号",
    "週刊少年チャンピオン グラップラー刃牙 1991",
    "週刊少年チャンピオン 1991 43",
    "チャンピオン 1991 43号",
    "グラップラー刃牙 チャンピオン",
    "週刊少年チャンピオン 1991年43号",
    "板垣恵介 チャンピオン 1991",
]

# Rakuma / Fril
RAKUMA_QUERIES = [
    "週刊少年チャンピオン 1991年43号",
    "週刊少年チャンピオン 1991 43号",
    "少年チャンピオン 1991年43号",
    "グラップラー刃牙 チャンピオン 1991",
    "刃牙 少年チャンピオン 1991",
    "チャンピオン 1991 43号",
    "板垣恵介 チャンピオン 1991 43",
    "週刊少年チャンピオン 1991 43 板垣",
    "グラップラー刃牙 連載開始 チャンピオン",
]


# ---------------------------------------------------------------------------
# Grading & relevance filters
# ---------------------------------------------------------------------------

GRADING_KEYWORDS = [
    'bgs', 'beckett', 'cgc', 'psa', 'cbcs', 'ace',
    'graded', 'grading', '鑑定', '鑑定品', 'グレーディング', 'スラブ', 'slab',
]

GRADE_8_PLUS = [
    'bgs 10', 'bgs 9.5', 'bgs 9', 'bgs 8.5', 'bgs 8',
    'cgc 10', 'cgc 9.9', 'cgc 9.8', 'cgc 9.6', 'cgc 9.4', 'cgc 9.2', 'cgc 9.0', 'cgc 8.5', 'cgc 8.0',
    'psa 10', 'psa 9', 'psa 8',
    'cbcs 10', 'cbcs 9.9', 'cbcs 9.8', 'cbcs 9.6', 'cbcs 9.4', 'cbcs 9.2', 'cbcs 9.0', 'cbcs 8.5', 'cbcs 8.0',
    'ace 10', 'ace 9', 'ace 8',
]


def is_graded(title):
    t = title.lower()
    return any(kw.lower() in t for kw in GRADING_KEYWORDS)


def is_grade_8_plus(title):
    t = title.lower()
    for grade in GRADE_8_PLUS:
        if grade in t:
            return True
    m = re.search(r'(?:bgs|cgc|psa|cbcs|ace)\s*(\d+\.?\d*)', t)
    if m:
        try:
            if float(m.group(1)) >= 8:
                return True
        except ValueError:
            pass
    return False


def is_wsc_1991_43(title):
    """Check if listing is the WSC 1991 #43 issue.

    Very broad matching — we want to catch everything that could be this issue.
    Matches on:
    - Champion magazine + 1991 + issue 43
    - Grappler Baki + champion/1991
    - Itagaki + champion + 1991
    """
    t = title.lower()
    t_orig = title

    has_champion = any(kw in t for kw in [
        'shonen champion', 'weekly champion', 'wsc', 'champion 1991',
    ]) or any(kw in t_orig for kw in [
        '週刊少年チャンピオン', '少年チャンピオン', 'チャンピオン',
    ])

    has_1991 = '1991' in t

    has_43 = bool(
        re.search(r'(?<!\d)43号', t_orig)
        or re.search(r'#43(?!\d)', t)
        or re.search(r'no\.?\s*43(?!\d)', t)
        or re.search(r'(?:^|[\s#＃])0*43(?:[号\s,.\-]|$)', t_orig)
    )

    # Pattern 1: Champion + 1991 + #43
    if has_champion and has_1991 and has_43:
        return True

    # Pattern 2: Grappler Baki + champion or 1991
    has_baki = any(kw in t or kw in t_orig for kw in [
        'grappler baki', 'グラップラー刃牙', '刃牙', 'baki the grappler',
    ])
    if has_baki and (has_champion or has_1991):
        return True

    # Pattern 3: Itagaki + champion + 1991 + 43
    has_itagaki = any(kw in t or kw in t_orig for kw in [
        'itagaki', '板垣恵介', '板垣',
    ])
    if has_itagaki and has_champion and has_1991 and has_43:
        return True

    return False


# Exclusions
EXCLUDE_KEYWORDS = [
    'trading card', 'tcg', 'card game',
    'トレーディングカード', 'カードゲーム',
    'figure', 'figurine', 'statue', 'plush',
    'フィギュア', 'ぬいぐるみ',
    'dvd', 'blu-ray', 'bluray',
    'reprint', '復刻', '復刻版',
    '愛蔵版', '完全版', '文庫版', '新装版',
]


def should_exclude(title):
    t = title.lower()
    return any(kw.lower() in t for kw in EXCLUDE_KEYWORDS)


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
        if 'just a moment' not in title and 'checking' not in title and 'cloudflare' not in title:
            return True
    return False


# ---------------------------------------------------------------------------
# Platform search functions
# ---------------------------------------------------------------------------

def search_ebay(results):
    print("\n" + "=" * 60)
    print("SEARCHING: eBay")
    print("=" * 60)

    try:
        from scraper import EbayScraper
        scraper = EbayScraper()
    except ImportError:
        print("  Could not import EbayScraper, skipping eBay")
        return

    seen_ids = set()

    for query in EBAY_QUERIES:
        try:
            print(f"\n  Searching: {query}")
            listings = scraper.scrape_active_listings(query, max_pages=2, items_per_page=60)

            for listing in listings:
                item_id = listing.get('item_id')
                if not item_id or item_id in seen_ids:
                    continue
                seen_ids.add(item_id)

                title = listing.get('title', '')
                price = listing.get('price')
                link = listing.get('link', '')

                if should_exclude(title):
                    continue

                results.append({
                    'platform': 'eBay',
                    'title': title,
                    'price': f"${price}" if price else "N/A",
                    'price_raw': price,
                    'currency': 'USD',
                    'link': link,
                    'listing_type': listing.get('listing_type', 'unknown'),
                    'search_query': query,
                    'is_graded': is_graded(title),
                    'grade_8_plus': is_grade_8_plus(title),
                    'confirmed_43': is_wsc_1991_43(title),
                })
                tag = " [CONFIRMED #43]" if is_wsc_1991_43(title) else ""
                graded_tag = " [GRADED]" if is_graded(title) else ""
                print(f"    Found{tag}{graded_tag}: {title[:60]}... - ${price}")

        except Exception as e:
            print(f"    Error searching '{query}': {e}")
        time.sleep(2)


def search_fanatics(results):
    print("\n" + "=" * 60)
    print("SEARCHING: Fanatics Collect")
    print("=" * 60)

    try:
        from fanatics_scraper import FanaticsScraper
        scraper = FanaticsScraper()
    except ImportError:
        print("  Could not import FanaticsScraper, skipping")
        return

    seen_ids = set()

    for query in FANATICS_QUERIES:
        try:
            print(f"\n  Searching: {query}")
            listings = scraper.search_listings(query, max_pages=2)

            for listing in listings:
                lid = listing.get('listing_id', '')
                if lid in seen_ids:
                    continue
                seen_ids.add(lid)

                title = listing.get('title', '')
                price = listing.get('price')
                link = listing.get('link', '')

                if should_exclude(title):
                    continue

                results.append({
                    'platform': 'Fanatics Collect',
                    'title': title,
                    'price': f"${price}" if price else "N/A",
                    'price_raw': price,
                    'currency': 'USD',
                    'link': link,
                    'listing_type': listing.get('listing_type', 'unknown'),
                    'search_query': query,
                    'is_graded': is_graded(title),
                    'grade_8_plus': is_grade_8_plus(title),
                    'confirmed_43': is_wsc_1991_43(title),
                })
                tag = " [#43]" if is_wsc_1991_43(title) else ""
                print(f"    Found{tag}: {title[:60]}... - ${price}")

        except Exception as e:
            print(f"    Error searching '{query}': {e}")
        time.sleep(2)


def search_snkrdunk(results):
    print("\n" + "=" * 60)
    print("SEARCHING: SNKRDUNK")
    print("=" * 60)

    try:
        from snkrdunk_scraper import SnkrdunkScraper
        scraper = SnkrdunkScraper()
    except ImportError:
        print("  Could not import SnkrdunkScraper, skipping")
        return

    seen_ids = set()

    for query in SNKRDUNK_QUERIES:
        try:
            print(f"\n  Searching: {query}")
            listings = scraper.search_listings(query, max_pages=1)

            for listing in listings:
                lid = listing.get('listing_id', '')
                if lid in seen_ids:
                    continue
                seen_ids.add(lid)

                title = listing.get('title', '')
                price = listing.get('price')
                link = listing.get('link', '')

                if should_exclude(title):
                    continue

                results.append({
                    'platform': 'SNKRDUNK',
                    'title': title,
                    'price': f"¥{int(price):,}" if price else "N/A",
                    'price_raw': price,
                    'currency': 'JPY',
                    'link': link,
                    'listing_type': 'buy_now',
                    'search_query': query,
                    'is_graded': is_graded(title),
                    'grade_8_plus': is_grade_8_plus(title),
                    'confirmed_43': is_wsc_1991_43(title),
                })
                tag = " [#43]" if is_wsc_1991_43(title) else ""
                print(f"    Found{tag}: {title[:60]}... - ¥{price}")

        except Exception as e:
            print(f"    Error searching '{query}': {e}")
        time.sleep(2)


def search_magi(page, results):
    print("\n" + "=" * 60)
    print("SEARCHING: Magi (magi.camp)")
    print("=" * 60)

    seen_ids = set()

    for query in MAGI_QUERIES:
        try:
            encoded_query = quote(query)
            url = f"https://magi.camp/search?q={encoded_query}"

            print(f"\n  Searching: {query}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            items = page.query_selector_all('a[href*="/items/"], a[href*="/item/"], .item-card, [class*="ItemCard"], [class*="itemCard"]')
            if not items:
                items = page.query_selector_all('.search-result-item, .product-card, [class*="product"], [class*="card"]')

            for item in items[:30]:
                try:
                    href = item.get_attribute('href')
                    if not href:
                        link_el = item.query_selector('a')
                        if link_el:
                            href = link_el.get_attribute('href')
                    if not href:
                        continue

                    item_match = re.search(r'/items?/([a-zA-Z0-9_-]+)', href)
                    item_id = item_match.group(1) if item_match else href
                    if item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)

                    text = item.inner_text().strip()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    title_lines = [
                        l for l in lines
                        if not re.match(r'^[¥￥\$]?[\d,\.]+$', l.replace(',', '').replace('¥', '').replace('￥', ''))
                        and len(l) > 3
                    ]
                    title = title_lines[0][:120] if title_lines else item_id

                    if should_exclude(title):
                        continue

                    price = None
                    for line in lines:
                        m = re.search(r'[¥￥]([\d,]+)', line)
                        if m:
                            price = m.group(1)
                            break

                    full_link = f"https://magi.camp{href}" if not href.startswith('http') else href

                    results.append({
                        'platform': 'Magi',
                        'title': title,
                        'price': f"¥{price}" if price else "N/A",
                        'price_raw': float(price.replace(',', '')) if price else None,
                        'currency': 'JPY',
                        'link': full_link,
                        'listing_type': 'buy_now',
                        'search_query': query,
                        'is_graded': is_graded(title),
                        'grade_8_plus': is_grade_8_plus(title),
                        'confirmed_43': is_wsc_1991_43(title),
                    })
                    tag = " [#43]" if is_wsc_1991_43(title) else ""
                    print(f"    Found{tag}: {title[:60]}... - ¥{price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")
        time.sleep(2)


def search_mercari_japan(page, results):
    print("\n" + "=" * 60)
    print("SEARCHING: Mercari Japan")
    print("=" * 60)

    seen_ids = set()
    # Queries with 43 in them are specific enough to trust
    SPECIFIC_QUERIES = {q for q in MERCARI_QUERIES if '43' in q and '1991' in q}

    for query in MERCARI_QUERIES:
        is_specific = query in SPECIFIC_QUERIES
        try:
            encoded_query = quote(query)
            url = f"https://jp.mercari.com/search?keyword={encoded_query}&order=desc&sort=created_time&status=on_sale"

            print(f"\n  Searching: {query}  {'[specific]' if is_specific else '[broad]'}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            links = page.query_selector_all('a[href*="/item/"]')
            print(f"    Found {len(links)} item links on page")

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
                        and len(l) > 3
                    ]
                    title = title_lines[0][:120] if title_lines else item_id

                    if should_exclude(title):
                        continue
                    if not is_specific and not is_wsc_1991_43(title):
                        continue

                    price = None
                    price_raw = None
                    for line in lines:
                        m = re.search(r'[¥￥]([\d,]+)', line)
                        if m:
                            price = m.group(1)
                            try:
                                price_raw = float(price.replace(',', ''))
                            except ValueError:
                                pass
                            break
                        if re.match(r'^[\d,]+$', line.strip()) and len(line.strip()) >= 3:
                            price = line.strip()
                            try:
                                price_raw = float(price.replace(',', ''))
                            except ValueError:
                                pass
                            break

                    full_link = f"https://jp.mercari.com{href}" if not href.startswith('http') else href

                    results.append({
                        'platform': 'Mercari Japan',
                        'title': title,
                        'price': f"¥{price}" if price else "N/A",
                        'price_raw': price_raw,
                        'currency': 'JPY',
                        'link': full_link,
                        'listing_type': 'buy_now',
                        'search_query': query,
                        'is_graded': is_graded(title),
                        'grade_8_plus': is_grade_8_plus(title),
                        'confirmed_43': is_wsc_1991_43(title),
                    })
                    tag = " [#43]" if is_wsc_1991_43(title) else ""
                    graded_tag = " [GRADED]" if is_graded(title) else ""
                    print(f"    Found{tag}{graded_tag}: {title[:55]}... - ¥{price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")
        time.sleep(2)


def search_yahoo_auctions(page, results):
    print("\n" + "=" * 60)
    print("SEARCHING: Yahoo Auctions Japan")
    print("=" * 60)

    seen_titles = set()

    for query in YAHOO_QUERIES:
        try:
            encoded_query = quote(query)
            url = f"https://auctions.yahoo.co.jp/search/search?p={encoded_query}&va={encoded_query}&exflg=1&b=1&n=50"

            print(f"\n  Searching: {query}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            items = page.query_selector_all('.Product, .cf, [data-auction-id], .Product__titleLink')

            for item in items[:30]:
                try:
                    title_el = item.query_selector('.Product__titleLink, .Product__title a, a')
                    if not title_el:
                        continue

                    title = title_el.inner_text().strip()[:120]
                    href = title_el.get_attribute('href')

                    if should_exclude(title):
                        continue

                    title_key = title[:50]
                    if title_key in seen_titles:
                        continue
                    seen_titles.add(title_key)

                    price_el = item.query_selector('.Product__priceValue, .Product__price')
                    price_text = price_el.inner_text().strip() if price_el else "N/A"

                    price_raw = None
                    m = re.search(r'([\d,]+)', price_text)
                    if m:
                        try:
                            price_raw = float(m.group(1).replace(',', ''))
                        except ValueError:
                            pass

                    results.append({
                        'platform': 'Yahoo Auctions JP',
                        'title': title,
                        'price': price_text,
                        'price_raw': price_raw,
                        'currency': 'JPY',
                        'link': href or url,
                        'listing_type': 'auction',
                        'search_query': query,
                        'is_graded': is_graded(title),
                        'grade_8_plus': is_grade_8_plus(title),
                        'confirmed_43': is_wsc_1991_43(title),
                    })
                    tag = " [#43]" if is_wsc_1991_43(title) else ""
                    print(f"    Found{tag}: {title[:50]}... - {price_text}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")
        time.sleep(2)


def search_rakuma(page, results):
    print("\n" + "=" * 60)
    print("SEARCHING: Rakuma (ラクマ)")
    print("=" * 60)

    seen_ids = set()

    for query in RAKUMA_QUERIES:
        try:
            encoded_query = quote(query)
            url = f"https://fril.jp/search/{encoded_query}"

            print(f"\n  Searching: {query}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            items = page.query_selector_all('a[href*="/item/"], .item, [class*="Item"], [class*="product"]')

            for item in items[:30]:
                try:
                    href = item.get_attribute('href')
                    if not href:
                        link_el = item.query_selector('a')
                        if link_el:
                            href = link_el.get_attribute('href')
                    if not href or '/sign_in' in href or '/sign_up' in href:
                        continue

                    item_match = re.search(r'/item/(\w+)', href)
                    item_id = item_match.group(1) if item_match else href
                    if item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)

                    text = item.inner_text().strip()
                    if any(junk in text for junk in ['SOLD OUT', 'ログイン', '会員登録']):
                        continue

                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    title_lines = [
                        l for l in lines
                        if not re.match(r'^[¥￥]?[\d,\.]+$', l.replace(',', '').replace('¥', '').replace('￥', ''))
                        and len(l) > 3
                        and '%' not in l
                    ]
                    title = title_lines[0][:120] if title_lines else item_id

                    if should_exclude(title):
                        continue

                    price = None
                    for line in lines:
                        m = re.search(r'[¥￥]([\d,]+)', line)
                        if m:
                            price = m.group(1)
                            break

                    full_link = href if href.startswith('http') else f"https://fril.jp{href}"

                    results.append({
                        'platform': 'Rakuma',
                        'title': title,
                        'price': f"¥{price}" if price else "N/A",
                        'price_raw': float(price.replace(',', '')) if price else None,
                        'currency': 'JPY',
                        'link': full_link,
                        'listing_type': 'buy_now',
                        'search_query': query,
                        'is_graded': is_graded(title),
                        'grade_8_plus': is_grade_8_plus(title),
                        'confirmed_43': is_wsc_1991_43(title),
                    })
                    tag = " [#43]" if is_wsc_1991_43(title) else ""
                    print(f"    Found{tag}: {title[:60]}... - ¥{price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")
        time.sleep(2)


def search_mandarake(page, results):
    print("\n" + "=" * 60)
    print("SEARCHING: Mandarake")
    print("=" * 60)

    seen_titles = set()

    for query in MANDARAKE_QUERIES:
        try:
            encoded_query = quote(query)
            url = f"https://order.mandarake.co.jp/order/listPage/list?keyword={encoded_query}&lang=ja"

            print(f"\n  Searching: {query}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            items = page.query_selector_all('.block, .thumlarge, [class*="item"], a[href*="/item/"]')
            if not items:
                items = page.query_selector_all('.content a, .entry, li a')

            for item in items[:30]:
                try:
                    href = item.get_attribute('href')
                    if not href:
                        link_el = item.query_selector('a')
                        if link_el:
                            href = link_el.get_attribute('href')
                    if not href:
                        continue

                    text = item.inner_text().strip()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    title_lines = [l for l in lines if len(l) > 5]
                    title = title_lines[0][:120] if title_lines else ''

                    if not title or should_exclude(title):
                        continue

                    title_key = title[:50]
                    if title_key in seen_titles:
                        continue
                    seen_titles.add(title_key)

                    price = None
                    for line in lines:
                        m = re.search(r'[¥￥]([\d,]+)', line)
                        if m:
                            price = m.group(1)
                            break

                    full_link = href if href.startswith('http') else f"https://order.mandarake.co.jp{href}"

                    results.append({
                        'platform': 'Mandarake',
                        'title': title,
                        'price': f"¥{price}" if price else "N/A",
                        'price_raw': float(price.replace(',', '')) if price else None,
                        'currency': 'JPY',
                        'link': full_link,
                        'listing_type': 'buy_now',
                        'search_query': query,
                        'is_graded': is_graded(title),
                        'grade_8_plus': is_grade_8_plus(title),
                        'confirmed_43': is_wsc_1991_43(title),
                    })
                    tag = " [#43]" if is_wsc_1991_43(title) else ""
                    print(f"    Found{tag}: {title[:60]}... - ¥{price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")
        time.sleep(2)


def search_surugaya(page, results):
    print("\n" + "=" * 60)
    print("SEARCHING: Suruga-ya")
    print("=" * 60)

    seen_titles = set()

    for query in SURUGAYA_QUERIES:
        try:
            encoded_query = quote(query)
            url = f"https://www.suruga-ya.jp/search?category=&search_word={encoded_query}&rankBy=modificationtime%3Adescending"

            print(f"\n  Searching: {query}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            items = page.query_selector_all('.item, .item_box, [class*="product"], a[href*="/product/"]')
            if not items:
                items = page.query_selector_all('.search_result a, li a[href*="product"]')

            for item in items[:30]:
                try:
                    href = item.get_attribute('href')
                    if not href:
                        link_el = item.query_selector('a')
                        if link_el:
                            href = link_el.get_attribute('href')
                    if not href:
                        continue

                    text = item.inner_text().strip()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    title_lines = [l for l in lines if len(l) > 5]
                    title = title_lines[0][:120] if title_lines else ''

                    if not title or should_exclude(title):
                        continue

                    title_key = title[:50]
                    if title_key in seen_titles:
                        continue
                    seen_titles.add(title_key)

                    price = None
                    for line in lines:
                        m = re.search(r'[¥￥]([\d,]+)', line)
                        if m:
                            price = m.group(1)
                            break

                    full_link = href if href.startswith('http') else f"https://www.suruga-ya.jp{href}"

                    results.append({
                        'platform': 'Suruga-ya',
                        'title': title,
                        'price': f"¥{price}" if price else "N/A",
                        'price_raw': float(price.replace(',', '')) if price else None,
                        'currency': 'JPY',
                        'link': full_link,
                        'listing_type': 'buy_now',
                        'search_query': query,
                        'is_graded': is_graded(title),
                        'grade_8_plus': is_grade_8_plus(title),
                        'confirmed_43': is_wsc_1991_43(title),
                    })
                    tag = " [#43]" if is_wsc_1991_43(title) else ""
                    print(f"    Found{tag}: {title[:60]}... - ¥{price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")
        time.sleep(2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not PLAYWRIGHT_AVAILABLE:
        print("ERROR: Playwright is required.")
        return

    print("\n" + "#" * 60)
    print("# WSC 1991 #43 - GRAPPLER BAKI DEBUT SEARCH")
    print("# 週刊少年チャンピオン 1991年 43号 板垣恵介 グラップラー刃牙")
    print("# Significance: Grappler Baki serialization start")
    print("# Published: September 30, 1991")
    print("#" * 60)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # --- eBay ---
    try:
        search_ebay(results)
    except Exception as e:
        print(f"eBay search failed: {e}")

    # --- Fanatics ---
    try:
        search_fanatics(results)
    except Exception as e:
        print(f"Fanatics search failed: {e}")

    # --- SNKRDUNK ---
    try:
        search_snkrdunk(results)
    except Exception as e:
        print(f"SNKRDUNK search failed: {e}")

    # --- Japanese marketplaces (shared browser) ---
    with sync_playwright() as p:
        browser, context = create_browser_context(p)
        page = context.new_page()

        try:
            search_magi(page, results)
            search_mercari_japan(page, results)
            search_yahoo_auctions(page, results)
            search_rakuma(page, results)
            search_mandarake(page, results)
            search_surugaya(page, results)
        except Exception as e:
            print(f"Error during Japanese marketplace search: {e}")
        finally:
            browser.close()

    # --- Summary ---
    search_date = datetime.now().strftime('%Y-%m-%d')
    confirmed = [r for r in results if r.get('confirmed_43')]
    graded = [r for r in results if r.get('is_graded')]
    g8 = [r for r in results if r.get('grade_8_plus')]

    print("\n" + "=" * 60)
    print("SEARCH COMPLETE - SUMMARY")
    print("=" * 60)
    print(f"Total listings found: {len(results)}")
    print(f"Confirmed WSC 1991 #43: {len(confirmed)}")
    print(f"Graded copies: {len(graded)}")
    print(f"Grade 8+: {len(g8)}")

    if confirmed:
        print("\n--- CONFIRMED WSC 1991 #43 LISTINGS ---")
        for r in confirmed:
            graded_tag = " [GRADED]" if r.get('is_graded') else ""
            print(f"\n  [{r['platform']}]{graded_tag}")
            print(f"  Title: {r['title'][:80]}")
            print(f"  Price: {r['price']}")
            print(f"  Link: {r['link']}")

    if results and not confirmed:
        print("\n--- ALL RESULTS (none confirmed as #43) ---")
        by_platform = {}
        for r in results:
            p = r['platform']
            if p not in by_platform:
                by_platform[p] = []
            by_platform[p].append(r)

        for platform, listings in by_platform.items():
            print(f"\n{platform}: {len(listings)} results")
            for r in listings[:10]:
                print(f"  {r['title'][:60]} - {r['price']}")
                print(f"  {r['link']}")

    # --- Save JSON ---
    output_json = 'data/baki_wsc43_search_results.json'
    Path('data').mkdir(exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'search_date': datetime.now().isoformat(),
            'item': 'Weekly Shonen Champion 1991 #43 - Grappler Baki Debut (Itagaki Keisuke)',
            'item_jp': '週刊少年チャンピオン 1991年 43号 板垣恵介 グラップラー刃牙 連載開始',
            'published': 'September 30, 1991',
            'publisher': 'Akita Shoten (秋田書店)',
            'significance': 'Serialization start of Grappler Baki by Itagaki Keisuke',
            'total_results': len(results),
            'confirmed_43_count': len(confirmed),
            'graded_count': len(graded),
            'grade_8_plus_count': len(g8),
            'confirmed_43': confirmed,
            'all_results': results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nJSON saved to: {output_json}")

    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
