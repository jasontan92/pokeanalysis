"""
Search for Dragonair no rarity cards across Japanese marketplaces.
Japanese name: Hakuryuu
Search terms: old back/no rarity, first edition
"""

import re
import sys
import time
from datetime import datetime

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


def create_browser_context(playwright):
    """Create a stealth browser context."""
    browser = playwright.chromium.launch(
        headless=False,  # Required to bypass bot detection
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


def search_mercari_japan(page, results):
    """Search Mercari Japan for Dragonair no rarity."""
    print("\n" + "="*60)
    print("SEARCHING: Mercari Japan")
    print("="*60)

    # Search terms for Dragonair no rarity
    search_queries = [
        "ハクリュー 旧裏",           # Dragonair old back
        "ハクリュー 初版",           # Dragonair first edition
        "ハクリュー レアリティなし",   # Dragonair no rarity
        "dragonair 旧裏",           # English name + old back
    ]

    for query in search_queries:
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            url = f"https://jp.mercari.com/search?keyword={encoded_query}&order=desc&sort=created_time&status=on_sale"

            print(f"\nSearching: {query}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            # Extract listings
            links = page.query_selector_all('a[href*="/item/"]')
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

                    # Get title (filter out price lines)
                    title_lines = [
                        l for l in lines
                        if not l.startswith('SG') and not l.startswith('¥')
                        and not l.startswith('￥') and not re.match(r'^[\d,\.]+$', l.replace(',', ''))
                    ]
                    title = title_lines[0][:100] if title_lines else item_id

                    # Check if it's actually Dragonair-related
                    title_lower = title.lower()
                    if 'ハクリュー' not in title and 'dragonair' not in title_lower:
                        continue

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
                        'price': price,
                        'link': full_link,
                        'search_query': query
                    })
                    print(f"  ✓ Found: {title[:50]}... - ¥{price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"  Error searching '{query}': {e}")

        time.sleep(2)


def search_yahoo_auctions(page, results):
    """Search Yahoo Auctions Japan via direct access."""
    print("\n" + "="*60)
    print("SEARCHING: Yahoo Auctions Japan")
    print("="*60)

    search_queries = [
        "ハクリュー 旧裏",
        "ハクリュー ポケモンカード 初版",
        "dragonair no rarity pokemon",
    ]

    for query in search_queries:
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            # Direct Yahoo Auctions search
            url = f"https://auctions.yahoo.co.jp/search/search?p={encoded_query}&va={encoded_query}&exflg=1&b=1&n=50"

            print(f"\nSearching: {query}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            # Try to find auction items
            items = page.query_selector_all('.Product, .cf, [data-auction-id], .Product__titleLink')

            for item in items[:20]:  # Limit to first 20
                try:
                    # Try to get title
                    title_el = item.query_selector('.Product__titleLink, .Product__title a, a')
                    if not title_el:
                        continue

                    title = title_el.inner_text().strip()[:100]
                    href = title_el.get_attribute('href')

                    # Check if Dragonair related
                    if 'ハクリュー' not in title and 'dragonair' not in title.lower():
                        continue

                    # Try to get price
                    price_el = item.query_selector('.Product__priceValue, .Product__price')
                    price = price_el.inner_text().strip() if price_el else "N/A"

                    results.append({
                        'platform': 'Yahoo Auctions JP',
                        'title': title,
                        'price': price,
                        'link': href or url,
                        'search_query': query
                    })
                    print(f"  ✓ Found: {title[:50]}... - {price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"  Error searching '{query}': {e}")

        time.sleep(2)


def search_buyee(page, results):
    """Search Buyee (Yahoo Auctions proxy for international buyers)."""
    print("\n" + "="*60)
    print("SEARCHING: Buyee (Yahoo Auctions Proxy)")
    print("="*60)

    search_queries = [
        "ハクリュー 旧裏",
        "ハクリュー ポケモンカード",
    ]

    for query in search_queries:
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            url = f"https://buyee.jp/item/search/yahoo/auction?query={encoded_query}"

            print(f"\nSearching: {query}")
            page.goto(url, timeout=60000)
            wait_for_page_load(page)
            page.wait_for_timeout(3000)

            # Find item cards
            items = page.query_selector_all('.itemCard, .g-card, [class*="item"]')

            for item in items[:20]:
                try:
                    title_el = item.query_selector('a, .itemCard__title, .g-card__title')
                    if not title_el:
                        continue

                    title = title_el.inner_text().strip()[:100]
                    href = title_el.get_attribute('href')

                    if 'ハクリュー' not in title and 'dragonair' not in title.lower():
                        continue

                    price_el = item.query_selector('.itemCard__price, .g-card__price, [class*="price"]')
                    price = price_el.inner_text().strip() if price_el else "N/A"

                    results.append({
                        'platform': 'Buyee',
                        'title': title,
                        'price': price,
                        'link': f"https://buyee.jp{href}" if href and not href.startswith('http') else href,
                        'search_query': query
                    })
                    print(f"  ✓ Found: {title[:50]}... - {price}")

                except Exception:
                    continue

        except Exception as e:
            print(f"  Error searching '{query}': {e}")

        time.sleep(2)


def search_surugaya(page, results):
    """Search Suruga-ya for Dragonair cards."""
    print("\n" + "="*60)
    print("SEARCHING: Suruga-ya")
    print("="*60)

    try:
        import urllib.parse
        query = "ハクリュー ポケモンカード"
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.suruga-ya.jp/search?category=5&search_word={encoded_query}"

        print(f"\nSearching: {query}")
        page.goto(url, timeout=60000)
        wait_for_page_load(page)
        page.wait_for_timeout(3000)

        items = page.query_selector_all('.item, .product-item, [class*="item"]')

        for item in items[:20]:
            try:
                title_el = item.query_selector('a, .item_title, .title')
                if not title_el:
                    continue

                title = title_el.inner_text().strip()[:100]
                href = title_el.get_attribute('href')

                if 'ハクリュー' not in title:
                    continue

                price_el = item.query_selector('.price, [class*="price"]')
                price = price_el.inner_text().strip() if price_el else "N/A"

                results.append({
                    'platform': 'Suruga-ya',
                    'title': title,
                    'price': price,
                    'link': f"https://www.suruga-ya.jp{href}" if href and not href.startswith('http') else href,
                    'search_query': query
                })
                print(f"  ✓ Found: {title[:50]}... - {price}")

            except Exception:
                continue

    except Exception as e:
        print(f"  Error: {e}")


def search_cardrush(page, results):
    """Search Card Rush for Dragonair cards."""
    print("\n" + "="*60)
    print("SEARCHING: Card Rush")
    print("="*60)

    try:
        import urllib.parse
        query = "ハクリュー"
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.cardrush-pokemon.jp/product-list?keyword={encoded_query}"

        print(f"\nSearching: {query}")
        page.goto(url, timeout=60000)
        wait_for_page_load(page)
        page.wait_for_timeout(3000)

        items = page.query_selector_all('.product-item, .item, [class*="product"]')

        for item in items[:20]:
            try:
                title_el = item.query_selector('a, .product-title, .title')
                if not title_el:
                    continue

                title = title_el.inner_text().strip()[:100]
                href = title_el.get_attribute('href')

                if 'ハクリュー' not in title:
                    continue

                price_el = item.query_selector('.price, [class*="price"]')
                price = price_el.inner_text().strip() if price_el else "N/A"

                results.append({
                    'platform': 'Card Rush',
                    'title': title,
                    'price': price,
                    'link': href or url,
                    'search_query': query
                })
                print(f"  ✓ Found: {title[:50]}... - {price}")

            except Exception:
                continue

    except Exception as e:
        print(f"  Error: {e}")


def main():
    """Main search function."""
    if not PLAYWRIGHT_AVAILABLE:
        print("ERROR: Playwright is required. Install with:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return

    print("\n" + "#"*60)
    print("# DRAGONAIR NO RARITY SEARCH")
    print("# Japanese: ハクリュー (Hakuryuu)")
    print("# Looking for: 旧裏 (old back) / 初版 (first edition)")
    print("#"*60)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    with sync_playwright() as p:
        browser, context = create_browser_context(p)
        page = context.new_page()

        try:
            # Search all Japanese marketplaces
            search_mercari_japan(page, results)
            search_yahoo_auctions(page, results)
            search_buyee(page, results)
            search_surugaya(page, results)
            search_cardrush(page, results)

        except Exception as e:
            print(f"Error during search: {e}")
        finally:
            browser.close()

    # Print summary
    print("\n" + "="*60)
    print("SEARCH COMPLETE - SUMMARY")
    print("="*60)
    print(f"Total listings found: {len(results)}")

    if results:
        # Group by platform
        by_platform = {}
        for r in results:
            platform = r['platform']
            if platform not in by_platform:
                by_platform[platform] = []
            by_platform[platform].append(r)

        for platform, listings in by_platform.items():
            print(f"\n{platform}: {len(listings)} listings")
            for listing in listings:
                print(f"  • {listing['title'][:60]}")
                print(f"    Price: {listing['price']}")
                print(f"    Link: {listing['link']}")
    else:
        print("\nNo Dragonair no rarity listings found.")
        print("This is a rare card - keep checking!")

    # Save results
    if results:
        import json
        output_file = 'data/dragonair_search_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'search_date': datetime.now().isoformat(),
                'total_results': len(results),
                'results': results
            }, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to: {output_file}")

    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
