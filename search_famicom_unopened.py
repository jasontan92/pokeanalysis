"""
Search for UNOPENED (未開封) Famicom (ファミコン) games across platforms.

Target titles:
  - Zelda           : ゼルダの伝説
  - Mario           : スーパーマリオブラザーズ / マリオ
  - Dragon Quest    : ドラゴンクエスト / ドラクエ
  - Final Fantasy   : ファイナルファンタジー / FF

Hard requirements (a listing must mention BOTH):
  - ファミコン   (Famicom)
  - 未開封       (unopened / sealed)

Platforms: eBay, Mercari JP, Yahoo Auctions JP, Buyee (Yahoo proxy)
"""

import re
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

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
    print("WARNING: Playwright not installed. Run: pip install playwright && playwright install chromium")


# ---------------------------------------------------------------------------
# Target games
# ---------------------------------------------------------------------------

# Each game: display name + the Japanese title fragments that identify it.
GAMES = {
    'Zelda': ['ゼルダの伝説', 'ゼルダ', 'zelda'],
    'Mario': ['スーパーマリオブラザーズ', 'スーパーマリオ', 'マリオ', 'mario'],
    'Dragon Quest': ['ドラゴンクエスト', 'ドラクエ', 'dragon quest', 'dragon warrior'],
    'Final Fantasy': ['ファイナルファンタジー', 'ファイナルファンタジ', 'final fantasy'],
}

# A listing must be Famicom + one of our games + EITHER sealed OR VGA-graded.
REQUIRED_FAMICOM = ['ファミコン', 'famicom', 'family computer', 'fc']
REQUIRED_SEALED = ['未開封', 'sealed', 'unopened', 'new sealed', 'brand new sealed']
# VGA = Video Game Authority (grades/encapsulates sealed games).
REQUIRED_VGA = ['vga', 'video game authority']

# Exclude: Super Famicom (SNES) is a different console, and non-game merch.
EXCLUDE_KEYWORDS = [
    'スーパーファミコン', 'スーファミ', 'super famicom', 'super nintendo', 'snes', 'sfc',
    'キーホルダー', 'アクリル', 'ストラップ', 'ぬいぐるみ', 'フィギュア',
    'tシャツ', 'ポスター', 'カード', 'シール', 'attaché', 'グッズ',
    'keychain', 'keyholder', 'strap', 'figure', 'plush', 'poster', 'sticker',
]


# ---------------------------------------------------------------------------
# Search queries per platform
# ---------------------------------------------------------------------------

# Japanese marketplaces: include ファミコン + (未開封 or VGA) + title.
MERCARI_QUERIES = [
    # Unopened
    "ファミコン 未開封 ゼルダの伝説",
    "ファミコン 未開封 スーパーマリオブラザーズ",
    "ファミコン 未開封 マリオ",
    "ファミコン 未開封 ドラゴンクエスト",
    "ファミコン 未開封 ドラクエ",
    "ファミコン 未開封 ファイナルファンタジー",
    # VGA graded
    "ファミコン VGA ゼルダの伝説",
    "ファミコン VGA マリオ",
    "ファミコン VGA ドラゴンクエスト",
    "ファミコン VGA ファイナルファンタジー",
]

YAHOO_QUERIES = list(MERCARI_QUERIES)
BUYEE_QUERIES = list(MERCARI_QUERIES)

# eBay: VGA-graded only (English). No Japanese / unopened queries here.
EBAY_QUERIES = [
    "famicom vga zelda",
    "famicom vga mario",
    "famicom vga dragon quest",
    "famicom vga final fantasy",
]


# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------

def _has_any(text, keywords):
    t = text.lower()
    return any(kw.lower() in t for kw in keywords)


def is_famicom(title):
    """Title indicates a Famicom item."""
    return _has_any(title, REQUIRED_FAMICOM)


def is_sealed(title):
    """Title indicates the item is unopened / sealed."""
    return _has_any(title, REQUIRED_SEALED)


def is_vga(title):
    """Title indicates a VGA (Video Game Authority) graded copy."""
    return _has_any(title, REQUIRED_VGA)


def matched_game(title):
    """Return the display name of the target game this title matches, or None."""
    t = title.lower()
    for name, fragments in GAMES.items():
        for frag in fragments:
            if frag.lower() in t:
                return name
    return None


def should_exclude(title):
    """Exclude Super Famicom (SNES) items and non-game merchandise."""
    return _has_any(title, EXCLUDE_KEYWORDS)


def is_target(title):
    """A listing qualifies if it is Famicom + one of our games + (sealed OR VGA).

    Returns (ok, game, condition) where condition is 'VGA' or 'sealed'.
    VGA takes precedence in labeling (a VGA copy is also sealed).
    """
    if should_exclude(title):
        return False, None, None
    game = matched_game(title)
    if not game:
        return False, None, None
    if not is_famicom(title):
        return False, None, None
    if is_vga(title):
        return True, game, 'VGA'
    if is_sealed(title):
        return True, game, 'sealed'
    return False, None, None


# ---------------------------------------------------------------------------
# Browser helpers
# ---------------------------------------------------------------------------

def create_browser_context(playwright):
    """Create a stealth browser context."""
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
    """Wait for page to fully load, handling Cloudflare challenges."""
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
    """Search eBay for unopened Famicom games."""
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
            listings = scraper.scrape_active_listings(query, max_pages=1, items_per_page=60)

            for listing in listings:
                item_id = listing.get('item_id')
                if not item_id or item_id in seen_ids:
                    continue
                seen_ids.add(item_id)

                title = listing.get('title', '')
                price = listing.get('price')
                link = listing.get('link', '')
                listing_type = listing.get('listing_type', 'unknown')

                ok, game, condition = is_target(title)
                if not ok:
                    continue
                # eBay is VGA-only.
                if condition != 'VGA':
                    continue

                results.append({
                    'platform': 'eBay',
                    'game': game,
                    'condition': condition,
                    'title': title,
                    'price': f"${price}" if price else "N/A",
                    'price_raw': price,
                    'currency': 'USD',
                    'link': link,
                    'listing_type': listing_type,
                    'search_query': query,
                })
                print(f"    [{game}/{condition}] {title[:55]}... - ${price}")

        except Exception as e:
            print(f"    Error searching '{query}': {e}")

        time.sleep(2)


def search_mercari_japan(page, results):
    """Search Mercari Japan for unopened Famicom games."""
    print("\n" + "=" * 60)
    print("SEARCHING: Mercari Japan")
    print("=" * 60)

    seen_ids = set()

    for query in MERCARI_QUERIES:
        try:
            encoded_query = quote(query)
            url = f"https://jp.mercari.com/search?keyword={encoded_query}&order=desc&sort=created_time&status=on_sale"

            print(f"\n  Searching: {query}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            links = page.query_selector_all('a[href*="/item/"]')

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
                        if not l.startswith('SG') and not l.startswith('¥')
                        and not l.startswith('￥') and not re.match(r'^[\d,\.]+$', l.replace(',', ''))
                    ]
                    title = title_lines[0][:120] if title_lines else item_id

                    ok, game, condition = is_target(title)
                    if not ok:
                        continue

                    price = None
                    for line in lines:
                        price_match = re.search(r'(?:SG\$|[¥￥])?([\d,]+)', line)
                        if price_match and ('¥' in line or '￥' in line or line.startswith('SG')):
                            price = price_match.group(1)
                            break

                    full_link = f"https://jp.mercari.com{href}" if not href.startswith('http') else href

                    results.append({
                        'platform': 'Mercari Japan',
                        'game': game,
                        'condition': condition,
                        'title': title,
                        'price': f"¥{price}" if price else "N/A",
                        'price_raw': float(price.replace(',', '')) if price else None,
                        'currency': 'JPY',
                        'link': full_link,
                        'listing_type': 'buy_now',
                        'search_query': query,
                    })
                    print(f"    [{game}/{condition}] {title[:50]}... - ¥{price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")

        time.sleep(2)


def search_yahoo_auctions(page, results):
    """Search Yahoo Auctions Japan for unopened Famicom games."""
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

                    ok, game, condition = is_target(title)
                    if not ok:
                        continue

                    title_key = title[:50]
                    if title_key in seen_titles:
                        continue
                    seen_titles.add(title_key)

                    price_el = item.query_selector('.Product__priceValue, .Product__price')
                    price = price_el.inner_text().strip() if price_el else "N/A"

                    results.append({
                        'platform': 'Yahoo Auctions JP',
                        'game': game,
                        'condition': condition,
                        'title': title,
                        'price': price,
                        'price_raw': None,
                        'currency': 'JPY',
                        'link': href or url,
                        'listing_type': 'auction',
                        'search_query': query,
                    })
                    print(f"    [{game}/{condition}] {title[:50]}... - {price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")

        time.sleep(2)


def search_buyee(page, results):
    """Search Buyee (Yahoo Auctions proxy) for unopened Famicom games."""
    print("\n" + "=" * 60)
    print("SEARCHING: Buyee (Yahoo Auctions Proxy)")
    print("=" * 60)

    seen_titles = set()

    for query in BUYEE_QUERIES:
        try:
            encoded_query = quote(query)
            url = f"https://buyee.jp/item/search/yahoo/auction?query={encoded_query}"

            print(f"\n  Searching: {query}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            items = page.query_selector_all('.itemCard, .g-card, [class*="item"]')

            for item in items[:30]:
                try:
                    title_el = item.query_selector('a, .itemCard__title, .g-card__title')
                    if not title_el:
                        continue

                    title = title_el.inner_text().strip()[:120]
                    href = title_el.get_attribute('href')

                    ok, game, condition = is_target(title)
                    if not ok:
                        continue

                    title_key = title[:50]
                    if title_key in seen_titles:
                        continue
                    seen_titles.add(title_key)

                    price_el = item.query_selector('.itemCard__price, .g-card__price, [class*="price"]')
                    price = price_el.inner_text().strip() if price_el else "N/A"

                    results.append({
                        'platform': 'Buyee',
                        'game': game,
                        'condition': condition,
                        'title': title,
                        'price': price,
                        'price_raw': None,
                        'currency': 'JPY',
                        'link': f"https://buyee.jp{href}" if href and not href.startswith('http') else href,
                        'listing_type': 'auction',
                        'search_query': query,
                    })
                    print(f"    [{game}/{condition}] {title[:50]}... - {price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")

        time.sleep(2)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def generate_markdown(results, search_date):
    """Generate a markdown report from search results."""
    by_platform = {}
    by_game = {}
    for r in results:
        by_platform.setdefault(r['platform'], []).append(r)
        by_game.setdefault(r['game'], []).append(r)

    total = len(results)

    md = []
    vga_count = sum(1 for r in results if r.get('condition') == 'VGA')
    sealed_count = sum(1 for r in results if r.get('condition') == 'sealed')

    md.append("# Unopened / VGA Famicom Games - Search Results\n")
    md.append(f"**Search Date:** {search_date}")
    md.append(f"**Required keywords:** ファミコン (Famicom) + 未開封 (unopened) OR VGA (graded)")
    md.append(f"**Target titles:** Zelda / Mario / Dragon Quest / Final Fantasy")
    md.append(f"**Total Listings:** {total}  ({sealed_count} sealed, {vga_count} VGA)")
    md.append("")
    md.append("---\n")

    # Summary by game
    md.append("## Summary by Game\n")
    md.append("| Game | Sealed | VGA | Total |")
    md.append("|------|--------|-----|-------|")
    for game in GAMES:
        g = by_game.get(game, [])
        s = sum(1 for r in g if r.get('condition') == 'sealed')
        v = sum(1 for r in g if r.get('condition') == 'VGA')
        md.append(f"| {game} | {s} | {v} | {len(g)} |")
    md.append(f"| **Total** | **{sealed_count}** | **{vga_count}** | **{total}** |")
    md.append("")

    # Summary by platform
    md.append("## Summary by Platform\n")
    md.append("| Platform | Listings |")
    md.append("|----------|----------|")
    for platform, listings in by_platform.items():
        md.append(f"| {platform} | {len(listings)} |")
    md.append("")
    md.append("---\n")

    # Per-game sections
    for game in GAMES:
        listings = by_game.get(game, [])
        if not listings:
            continue
        md.append(f"## {game}\n")
        md.append("| Platform | Cond | Title | Price | Type | Link |")
        md.append("|----------|------|-------|-------|------|------|")
        for r in sorted(listings, key=lambda x: x.get('condition') != 'VGA'):
            title = (r['title'][:80] if r['title'] else "N/A").replace('|', '\\|')
            md.append(f"| {r['platform']} | {r.get('condition', '')} | {title} | {r.get('price', 'N/A')} | {r.get('listing_type', '')} | [View]({r.get('link', '')}) |")
        md.append("")

    md.append("---\n")
    md.append("## Search Terms Used\n")
    for section_name, queries in [
        ("eBay", EBAY_QUERIES),
        ("Mercari Japan", MERCARI_QUERIES),
        ("Yahoo Auctions Japan", YAHOO_QUERIES),
        ("Buyee", BUYEE_QUERIES),
    ]:
        md.append(f"### {section_name}")
        for q in queries:
            md.append(f"- `{q}`")
        md.append("")

    md.append("---\n")
    md.append("## Notes\n")
    md.append("- `ファミコン` = Famicom (Family Computer)")
    md.append("- `未開封` = mikaifuu (unopened / factory sealed)")
    md.append("- `ゼルダの伝説` = The Legend of Zelda")
    md.append("- `スーパーマリオブラザーズ` = Super Mario Bros.")
    md.append("- `ドラゴンクエスト` / `ドラクエ` = Dragon Quest")
    md.append("- `ファイナルファンタジー` = Final Fantasy")
    md.append("- **VGA** = Video Game Authority (grades & encapsulates sealed games)")
    md.append("- Listings must contain ファミコン + a target title + EITHER 未開封 OR VGA.")
    md.append("")
    md.append("*Generated by search_famicom_unopened.py*")

    return '\n'.join(md)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Main search function."""
    if not PLAYWRIGHT_AVAILABLE:
        print("ERROR: Playwright is required. Install with:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return

    print("\n" + "#" * 60)
    print("# UNOPENED FAMICOM GAMES SEARCH")
    print("# ファミコン 未開封 (ゼルダ / マリオ / ドラクエ / FF)")
    print("#" * 60)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # --- eBay (uses its own browser via EbayScraper) ---
    try:
        search_ebay(results)
    except Exception as e:
        print(f"eBay search failed: {e}")

    # --- Japanese marketplaces (fresh browser each, so one crash won't
    #     kill the others) ---
    for search_fn in (search_mercari_japan, search_yahoo_auctions, search_buyee):
        with sync_playwright() as p:
            browser, context = create_browser_context(p)
            page = context.new_page()
            try:
                search_fn(page, results)
            except Exception as e:
                print(f"  {search_fn.__name__} failed: {e}")
            finally:
                try:
                    browser.close()
                except Exception:
                    pass

    # --- Print summary ---
    search_date = datetime.now().strftime('%Y-%m-%d')

    print("\n" + "=" * 60)
    print("SEARCH COMPLETE - SUMMARY")
    print("=" * 60)
    print(f"Total listings found: {len(results)}")

    if results:
        by_platform = {}
        for r in results:
            by_platform.setdefault(r['platform'], []).append(r)

        for platform, listings in by_platform.items():
            print(f"\n{platform}: {len(listings)} listings")
            for listing in listings:
                print(f"  [{listing['game']}/{listing.get('condition')}] {listing['title'][:55]}")
                print(f"              Price: {listing['price']}")
                print(f"              Link: {listing['link']}")
    else:
        print("\nNo unopened Famicom listings found for the target games.")

    # --- Save JSON ---
    output_json = 'data/famicom_unopened_search_results.json'
    Path('data').mkdir(exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'search_date': datetime.now().isoformat(),
            'total_results': len(results),
            'results': results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nJSON results saved to: {output_json}")

    # --- Save markdown report ---
    output_md = 'price_analysis/famicom_unopened_search.md'
    Path('price_analysis').mkdir(exist_ok=True)
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(generate_markdown(results, search_date))
    print(f"Markdown report saved to: {output_md}")

    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
