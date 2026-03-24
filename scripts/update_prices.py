#!/usr/bin/env python3
"""
ScopeDeals Price Updater
========================
Fetches live prices from Amazon Creators API + web scraping.
Updates data/products.json with current prices.
Run by GitHub Actions on a weekly schedule.
"""

import json
import re
import os
import time
import logging
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Install deps with: pip install requests beautifulsoup4 lxml")
    exit(1)

try:
    from amazon_creatorsapi import AmazonCreatorsApi, Country
    HAS_AMAZON = True
except ImportError:
    HAS_AMAZON = False

# ── Config
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
HISTORY_FILE = DATA_DIR / "price_history.json"

TIMEOUT = 15
DELAY = 2
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("updater")


def load_products():
    with open(PRODUCTS_FILE) as f:
        return json.load(f)


def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2)
    log.info(f"Saved {len(products)} products to {PRODUCTS_FILE}")


def fetch_amazon_prices(products):
    """Fetch prices from Amazon Creators API for products with ASINs."""
    if not HAS_AMAZON:
        log.warning("python-amazon-paapi not installed, skipping Amazon")
        return {}

    cred_id = os.getenv("AMAZON_CREDENTIAL_ID", "")
    cred_secret = os.getenv("AMAZON_CREDENTIAL_SECRET", "")
    tag = os.getenv("AMAZON_AFFILIATE_TAG", "")

    if not cred_id or not cred_secret:
        log.warning("Amazon API credentials not set, skipping")
        return {}

    results = {}
    asin_map = {}
    for p in products:
        asin = p.get("asin")
        if asin:
            asin_map[asin] = p["id"]

    if not asin_map:
        return {}

    try:
        api = AmazonCreatorsApi(
            credential_id=cred_id,
            credential_secret=cred_secret,
            version="2.2",
            tag=tag,
            country=Country.US,
        )

        asin_list = list(asin_map.keys())
        for i in range(0, len(asin_list), 10):
            batch = asin_list[i:i+10]
            log.info(f"Amazon API: fetching {len(batch)} ASINs")
            try:
                items = api.get_items(batch)
                for item in items:
                    asin = item.asin
                    if asin not in asin_map:
                        continue
                    pid = asin_map[asin]
                    try:
                        listings = item.offers.listings if hasattr(item, 'offers') and item.offers else []
                        if listings and hasattr(listings[0], 'price') and hasattr(listings[0].price, 'amount'):
                            price = float(listings[0].price.amount)
                            url = getattr(item, 'detail_page_url', None) or f"https://amazon.com/dp/{asin}?tag={tag}"
                            results[pid] = {"price": price, "affiliateUrl": url}
                            log.info(f"  ✓ ID {pid}: ${price:.2f}")
                    except Exception:
                        pass
            except Exception as e:
                log.error(f"  Amazon batch error: {e}")
            time.sleep(1)

    except Exception as e:
        log.error(f"Amazon API error: {e}")

    return results


def scrape_price(url, name):
    """Extract price from a retailer product page using JSON-LD structured data."""
    headers = {"User-Agent": UA, "Accept": "text/html"}
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Try JSON-LD (most reliable)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and item.get("@type") in ("Product", "IndividualProduct"):
                        offers = item.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}
                        p = offers.get("price") or offers.get("lowPrice")
                        if p:
                            return float(p)
            except (json.JSONDecodeError, ValueError, TypeError):
                continue

        # Try meta tags
        for attr in ["product:price:amount", "og:price:amount"]:
            tag = soup.find("meta", {"property": attr})
            if tag and tag.get("content"):
                try:
                    return float(tag["content"])
                except ValueError:
                    pass

        # Regex fallback
        for pattern in [r'"price"\s*:\s*"?([\d,]+\.?\d*)"?', r'data-price="([\d,]+\.?\d*)"']:
            m = re.search(pattern, resp.text)
            if m:
                try:
                    val = float(m.group(1).replace(",", ""))
                    if 10 < val < 50000:
                        return val
                except ValueError:
                    pass

        log.warning(f"  ✗ No price found: {name}")
        return None

    except Exception as e:
        log.error(f"  Scrape error for {name}: {e}")
        return None


def fetch_scraped_prices(products):
    """Scrape prices for products with scrapeUrl fields."""
    results = {}
    for p in products:
        url = p.get("scrapeUrl")
        if not url:
            continue
        log.info(f"  Scraping: {p['name']}")
        price = scrape_price(url, p["name"])
        if price and price > 0:
            results[p["id"]] = {"price": price}
            log.info(f"  ✓ {p['name']}: ${price:.2f}")
        time.sleep(DELAY)
    return results


def log_history(updates, products):
    """Append price updates to history log."""
    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            pass

    name_map = {p["id"]: p["name"] for p in products}
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "updates": {str(pid): {"name": name_map.get(pid, "?"), "price": d["price"]} for pid, d in updates.items()},
    }
    history.append(entry)
    if len(history) > 500:
        history = history[-500:]
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def main():
    log.info("=" * 50)
    log.info("ScopeDeals Price Updater")
    log.info("=" * 50)

    products = load_products()
    all_updates = {}

    # Amazon
    log.info("\n🛒 Fetching Amazon prices...")
    amazon = fetch_amazon_prices(products)
    all_updates.update(amazon)

    # Scraping
    log.info("\n🌐 Scraping retailer prices...")
    scraped = fetch_scraped_prices(products)
    all_updates.update(scraped)

    # Apply updates
    if all_updates:
        for p in products:
            if p["id"] in all_updates:
                upd = all_updates[p["id"]]
                p["price"] = upd["price"]
                if "affiliateUrl" in upd:
                    p["affiliateUrl"] = upd["affiliateUrl"]
                p["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%d")

        save_products(products)
        log_history(all_updates, products)
        log.info(f"\n✅ Updated {len(all_updates)} prices")
    else:
        log.warning("\n⚠️ No prices updated")

    log.info(f"Total products: {len(products)}")
    log.info("=" * 50)


if __name__ == "__main__":
    main()
