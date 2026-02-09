"""
Search for 1996 CoroCoro glossy Pikachu and Jigglypuff cards across all platforms.
These are promo cards distributed via CoroCoro Comic magazine with a distinctive glossy finish.
Japanese: コロコロコミック付録 ピカチュウ / プリン

Searches each platform separately since the main "1996 no rarity" search won't find these.
"""

import re
import sys
import json
import time
import hashlib
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
    print("WARNING: Playwright not installed. Run: pip install playwright && playwright install chromium")


# ---------------------------------------------------------------------------
# Target cards - search terms per platform
# ---------------------------------------------------------------------------

# eBay (English-language)
EBAY_QUERIES = [
    "corocoro pikachu glossy 1996",
    "corocoro jigglypuff glossy 1996",
    "corocoro pikachu promo pokemon japanese",
    "corocoro jigglypuff promo pokemon japanese",
    "corocoro glossy pikachu pokemon",
    "corocoro glossy jigglypuff pokemon",
    "pokemon pikachu vending glossy 1996",
    "pokemon jigglypuff vending glossy 1996",
]

# Fanatics Collect (English-language)
FANATICS_QUERIES = [
    "corocoro pikachu",
    "corocoro jigglypuff",
    "corocoro glossy pokemon",
    "pikachu glossy promo 1996",
    "jigglypuff glossy promo 1996",
]

# Mercari Japan (Japanese-language)
MERCARI_QUERIES = [
    "コロコロ ピカチュウ ポケモンカード",        # CoroCoro Pikachu Pokemon card
    "コロコロ プリン ポケモンカード",            # CoroCoro Jigglypuff Pokemon card
    "コロコロコミック ピカチュウ",              # CoroCoro Comic Pikachu
    "コロコロコミック プリン",                  # CoroCoro Comic Jigglypuff
    "ピカチュウ コロコロ 付録",                # Pikachu CoroCoro appendix
    "プリン コロコロ 付録",                    # Jigglypuff CoroCoro appendix
    "ピカチュウ 光沢 旧裏",                   # Pikachu glossy old back
    "プリン 光沢 旧裏",                       # Jigglypuff glossy old back
]

# Yahoo Auctions Japan
YAHOO_QUERIES = [
    "コロコロ ピカチュウ ポケモンカード",
    "コロコロ プリン ポケモンカード",
    "コロコロコミック ピカチュウ 付録",
    "コロコロコミック プリン 付録",
]

# Buyee (Yahoo Auctions proxy)
BUYEE_QUERIES = [
    "コロコロ ピカチュウ ポケモンカード",
    "コロコロ プリン ポケモンカード",
]

# Keywords that indicate a listing is relevant to the target cards
RELEVANT_KEYWORDS = [
    'コロコロ', 'corocoro', 'coro coro',
    'ピカチュウ', 'pikachu',
    'プリン', 'jigglypuff', 'pudding',
    '光沢', 'glossy', 'gloss',
    '付録', 'promo', 'appendix',
]


def is_relevant(title):
    """Check if a listing title is relevant to CoroCoro glossy Pikachu/Jigglypuff."""
    t = title.lower()
    has_corocoro = any(k in t for k in ['コロコロ', 'corocoro', 'coro coro', 'coro-coro'])
    has_glossy = any(k in t for k in ['光沢', 'glossy', 'gloss', 'vending'])
    has_pikachu = any(k in t for k in ['ピカチュウ', 'pikachu'])
    has_jigglypuff = any(k in t for k in ['プリン', 'jigglypuff', 'pudding'])
    has_pokemon = has_pikachu or has_jigglypuff

    # Must mention at least one of the target Pokemon
    if not has_pokemon:
        return False
    # Must mention CoroCoro or glossy/vending
    if has_corocoro or has_glossy:
        return True
    # Also accept if it has 付録 (appendix/supplement)
    if '付録' in t:
        return True
    return False


# ---------------------------------------------------------------------------
# Browser helpers (shared with search_dragonair.py pattern)
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
    """Search eBay for CoroCoro glossy Pikachu and Jigglypuff."""
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

                results.append({
                    'platform': 'eBay',
                    'title': title,
                    'price': f"${price}" if price else "N/A",
                    'link': link,
                    'listing_type': listing_type,
                    'search_query': query,
                })
                print(f"    Found: {title[:60]}... - ${price}")

        except Exception as e:
            print(f"    Error searching '{query}': {e}")

        time.sleep(2)


def search_fanatics(results):
    """Search Fanatics Collect for CoroCoro glossy Pikachu and Jigglypuff."""
    print("\n" + "=" * 60)
    print("SEARCHING: Fanatics Collect")
    print("=" * 60)

    try:
        from fanatics_scraper import FanaticsScraper
        scraper = FanaticsScraper()
    except ImportError:
        print("  Could not import FanaticsScraper, skipping Fanatics")
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
                listing_type = listing.get('listing_type', 'unknown')

                results.append({
                    'platform': 'Fanatics Collect',
                    'title': title,
                    'price': f"${price}" if price else "N/A",
                    'link': link,
                    'listing_type': listing_type,
                    'search_query': query,
                })
                print(f"    Found: {title[:60]}... - ${price}")

        except Exception as e:
            print(f"    Error searching '{query}': {e}")

        time.sleep(2)


def search_mercari_japan(page, results):
    """Search Mercari Japan for CoroCoro glossy Pikachu and Jigglypuff."""
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
                    title = title_lines[0][:100] if title_lines else item_id

                    # Get price
                    price = None
                    for line in lines:
                        price_match = re.search(r'(?:SG\$|[¥￥])?([\d,]+)', line)
                        if price_match and ('¥' in line or '￥' in line or line.startswith('SG')):
                            price = price_match.group(1)
                            break

                    full_link = f"https://jp.mercari.com{href}" if not href.startswith('http') else href

                    results.append({
                        'platform': 'Mercari Japan',
                        'title': title,
                        'price': f"¥{price}" if price else "N/A",
                        'link': full_link,
                        'search_query': query,
                    })
                    print(f"    Found: {title[:50]}... - ¥{price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")

        time.sleep(2)


def search_yahoo_auctions(page, results):
    """Search Yahoo Auctions Japan for CoroCoro glossy cards."""
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

            for item in items[:20]:
                try:
                    title_el = item.query_selector('.Product__titleLink, .Product__title a, a')
                    if not title_el:
                        continue

                    title = title_el.inner_text().strip()[:100]
                    href = title_el.get_attribute('href')

                    title_key = title[:50]
                    if title_key in seen_titles:
                        continue
                    seen_titles.add(title_key)

                    price_el = item.query_selector('.Product__priceValue, .Product__price')
                    price = price_el.inner_text().strip() if price_el else "N/A"

                    results.append({
                        'platform': 'Yahoo Auctions JP',
                        'title': title,
                        'price': price,
                        'link': href or url,
                        'search_query': query,
                    })
                    print(f"    Found: {title[:50]}... - {price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"    Error searching '{query}': {e}")

        time.sleep(2)


def search_buyee(page, results):
    """Search Buyee (Yahoo Auctions proxy) for CoroCoro glossy cards."""
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

            for item in items[:20]:
                try:
                    title_el = item.query_selector('a, .itemCard__title, .g-card__title')
                    if not title_el:
                        continue

                    title = title_el.inner_text().strip()[:100]
                    href = title_el.get_attribute('href')

                    title_key = title[:50]
                    if title_key in seen_titles:
                        continue
                    seen_titles.add(title_key)

                    price_el = item.query_selector('.itemCard__price, .g-card__price, [class*="price"]')
                    price = price_el.inner_text().strip() if price_el else "N/A"

                    results.append({
                        'platform': 'Buyee',
                        'title': title,
                        'price': price,
                        'link': f"https://buyee.jp{href}" if href and not href.startswith('http') else href,
                        'search_query': query,
                    })
                    print(f"    Found: {title[:50]}... - {price}")

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
    # Group results by platform
    by_platform = {}
    for r in results:
        platform = r['platform']
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(r)

    total = len(results)

    md = []
    md.append("# CoroCoro Glossy Pikachu & Jigglypuff Search Results\n")
    md.append(f"**Search Date:** {search_date}")
    md.append("**Cards:** 1996 CoroCoro Comic Glossy Pikachu (コロコロ ピカチュウ) & Jigglypuff (コロコロ プリン)")
    md.append("**Type:** Promo / Appendix cards (付録) with glossy finish")
    md.append("")
    md.append("---\n")

    # Summary table
    md.append("## Summary\n")
    md.append("| Platform | Listings Found |")
    md.append("|----------|----------------|")
    for platform, listings in by_platform.items():
        md.append(f"| {platform} | {len(listings)} |")
    md.append(f"| **Total** | **{total}** |")
    md.append("")
    md.append("---\n")

    # eBay section
    if 'eBay' in by_platform:
        md.append("## eBay Listings\n")
        md.append("| Title | Price | Type | Link |")
        md.append("|-------|-------|------|------|")
        for r in by_platform['eBay']:
            title = r['title'][:80] if r['title'] else "N/A"
            price = r.get('price', 'N/A')
            ltype = r.get('listing_type', '')
            link = r.get('link', '')
            md.append(f"| {title} | {price} | {ltype} | [View]({link}) |")
        md.append("")

    # Fanatics section
    if 'Fanatics Collect' in by_platform:
        md.append("## Fanatics Collect Listings\n")
        md.append("| Title | Price | Type | Link |")
        md.append("|-------|-------|------|------|")
        for r in by_platform['Fanatics Collect']:
            title = r['title'][:80] if r['title'] else "N/A"
            price = r.get('price', 'N/A')
            ltype = r.get('listing_type', '')
            link = r.get('link', '')
            md.append(f"| {title} | {price} | {ltype} | [View]({link}) |")
        md.append("")

    # Mercari section
    if 'Mercari Japan' in by_platform:
        md.append("## Mercari Japan Listings\n")
        md.append("| Title | Price | Link |")
        md.append("|-------|-------|------|")
        for r in by_platform['Mercari Japan']:
            title = r['title'][:80] if r['title'] else "N/A"
            price = r.get('price', 'N/A')
            link = r.get('link', '')
            md.append(f"| {title} | {price} | [View]({link}) |")
        md.append("")

    # Yahoo Auctions section
    if 'Yahoo Auctions JP' in by_platform:
        md.append("## Yahoo Auctions Japan\n")
        md.append("| Title | Price | Link |")
        md.append("|-------|-------|------|")
        for r in by_platform['Yahoo Auctions JP']:
            title = r['title'][:80] if r['title'] else "N/A"
            price = r.get('price', 'N/A')
            link = r.get('link', '')
            md.append(f"| {title} | {price} | [View]({link}) |")
        md.append("")

    # Buyee section
    if 'Buyee' in by_platform:
        md.append("## Buyee (Yahoo Auctions Proxy)\n")
        md.append("| Title | Price | Link |")
        md.append("|-------|-------|------|")
        for r in by_platform['Buyee']:
            title = r['title'][:80] if r['title'] else "N/A"
            price = r.get('price', 'N/A')
            link = r.get('link', '')
            md.append(f"| {title} | {price} | [View]({link}) |")
        md.append("")

    md.append("---\n")

    # Search terms reference
    md.append("## Search Terms Used\n")
    md.append("### eBay (English)")
    for q in EBAY_QUERIES:
        md.append(f"- `{q}`")
    md.append("")
    md.append("### Fanatics Collect (English)")
    for q in FANATICS_QUERIES:
        md.append(f"- `{q}`")
    md.append("")
    md.append("### Mercari Japan (Japanese)")
    for q in MERCARI_QUERIES:
        md.append(f"- `{q}`")
    md.append("")
    md.append("### Yahoo Auctions / Buyee (Japanese)")
    for q in YAHOO_QUERIES:
        md.append(f"- `{q}`")
    md.append("")

    md.append("---\n")

    # Notes
    md.append("## Notes\n")
    md.append("- **CoroCoro glossy cards** were distributed as appendix (付録) promos in CoroCoro Comic magazine in 1996")
    md.append("- They have a distinctive **glossy/shiny finish** compared to normal cards")
    md.append("- Sometimes listed as **vending machine glossy** cards")
    md.append("- `コロコロ` = CoroCoro (magazine name)")
    md.append("- `付録` = furoku (appendix/supplement/bonus)")
    md.append("- `光沢` = koutaku (glossy/luster)")
    md.append("- `ピカチュウ` = Pikachu")
    md.append("- `プリン` = Purin (Jigglypuff)")
    md.append("")
    md.append("---\n")
    md.append("*Generated by search_corocoro.py*")

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
    print("# COROCORO GLOSSY PIKACHU & JIGGLYPUFF SEARCH")
    print("# ピカチュウ / プリン  (コロコロコミック 付録)")
    print("#" * 60)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # --- eBay (uses its own browser via EbayScraper) ---
    try:
        search_ebay(results)
    except Exception as e:
        print(f"eBay search failed: {e}")

    # --- Fanatics Collect (uses its own browser via FanaticsScraper) ---
    try:
        search_fanatics(results)
    except Exception as e:
        print(f"Fanatics search failed: {e}")

    # --- Japanese marketplaces (shared browser context) ---
    with sync_playwright() as p:
        browser, context = create_browser_context(p)
        page = context.new_page()

        try:
            search_mercari_japan(page, results)
            search_yahoo_auctions(page, results)
            search_buyee(page, results)
        except Exception as e:
            print(f"Error during Japanese marketplace search: {e}")
        finally:
            browser.close()

    # --- Print summary ---
    search_date = datetime.now().strftime('%Y-%m-%d')

    print("\n" + "=" * 60)
    print("SEARCH COMPLETE - SUMMARY")
    print("=" * 60)
    print(f"Total listings found: {len(results)}")

    if results:
        by_platform = {}
        for r in results:
            platform = r['platform']
            if platform not in by_platform:
                by_platform[platform] = []
            by_platform[platform].append(r)

        for platform, listings in by_platform.items():
            print(f"\n{platform}: {len(listings)} listings")
            for listing in listings:
                print(f"  - {listing['title'][:60]}")
                print(f"    Price: {listing['price']}")
                print(f"    Link: {listing['link']}")
    else:
        print("\nNo CoroCoro glossy listings found.")
        print("These are rare promo cards - keep checking!")

    # --- Save JSON ---
    output_json = 'data/corocoro_search_results.json'
    Path('data').mkdir(exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'search_date': datetime.now().isoformat(),
            'total_results': len(results),
            'results': results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nJSON results saved to: {output_json}")

    # --- Save markdown report ---
    output_md = 'price_analysis/corocoro_glossy_search.md'
    Path('price_analysis').mkdir(exist_ok=True)
    md_content = generate_markdown(results, search_date)
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Markdown report saved to: {output_md}")

    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
