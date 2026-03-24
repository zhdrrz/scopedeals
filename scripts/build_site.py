#!/usr/bin/env python3
"""
ScopeDeals Site Builder
=======================
Reads data/products.json and templates/site.html,
generates public/index.html with the product data injected.
"""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
PRODUCTS_FILE = ROOT / "data" / "products.json"
TEMPLATE_FILE = ROOT / "templates" / "site.html"
OUTPUT_FILE = ROOT / "public" / "index.html"
ADMIN_SRC = ROOT / "templates" / "admin.html"
ADMIN_OUT = ROOT / "public" / "admin.html"


def build():
    # Load products
    products = json.load(open(PRODUCTS_FILE))
    
    # Generate JS products array
    lines = []
    for p in products:
        flags = []
        if p.get("bestValue"):
            flags.append("bestValue:true")
        if p.get("editorsPick"):
            flags.append("editorsPick:true")
        flag_str = "," + ",".join(flags) if flags else ""

        line = (
            f'  {{id:{p["id"]},name:"{esc(p["name"])}",brand:"{esc(p["brand"])}",'
            f'category:"{p["category"]}",price:{p["price"]},msrp:{p["msrp"]},'
            f'\n   aperture:"{esc(p.get("aperture","—"))}",focalLength:"{esc(p.get("focalLength","—"))}",'
            f'fRatio:"{esc(p.get("fRatio","—"))}",sensor:"{esc(p.get("sensor","—"))}",'
            f'resolution:"{esc(p.get("resolution","—"))}",'
            f'\n   fov:"{esc(p.get("fov","—"))}",battery:"{esc(p.get("battery","—"))}",'
            f'storage:"{esc(p.get("storage","—"))}",weight:"{esc(p.get("weight","—"))}",'
            f'\n   highlight:"{esc(p.get("highlight",""))}",'
            f'\n   retailer:"{esc(p.get("retailer","Amazon"))}",'
            f'affiliateUrl:"{esc(p.get("affiliateUrl","#"))}"{flag_str}}},'
        )
        lines.append(line)

    products_js = "const products = [\n" + "\n\n".join(lines) + "\n];"
    timestamp = datetime.utcnow().strftime("%b %d, %Y %I:%M %p UTC")

    # Read template
    template = TEMPLATE_FILE.read_text(encoding="utf-8")

    # Inject products and timestamp
    html = template.replace("/* __PRODUCTS_DATA__ */", products_js)
    html = html.replace("__LAST_UPDATED__", timestamp)

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"✅ Built {OUTPUT_FILE} with {len(products)} products (updated {timestamp})")

    # Copy admin panel if it exists
    if ADMIN_SRC.exists():
        ADMIN_OUT.write_text(ADMIN_SRC.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"✅ Copied admin panel to {ADMIN_OUT}")


def esc(s):
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


if __name__ == "__main__":
    build()
