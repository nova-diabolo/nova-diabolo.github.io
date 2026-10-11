#!/usr/bin/env python3
"""
Stamp the stylesheet and script URLs with a hash of their contents.

GitHub Pages serves assets with `cache-control: max-age=600`, so for ten
minutes after a deploy a returning visitor can get the old CSS or JS against
the new HTML. Appending a content hash changes the URL whenever the file
changes, so the browser is forced to refetch, and nothing changes when it
doesn't.

Run this after editing assets/css/styles.css or assets/js/main.js, before
committing:  python3 tools/stamp-assets.py
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index.html", "thanks.html"]
ASSETS = ["assets/css/styles.css", "assets/js/main.js"]


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:8]


def main():
    stamps = {a: digest(a) for a in ASSETS}
    for page in PAGES:
        p = ROOT / page
        if not p.exists():
            continue
        html = original = p.read_text(encoding="utf-8")
        for asset, h in stamps.items():
            # match the asset with or without an existing ?v= stamp
            html = re.sub(re.escape(asset) + r'(\?v=[0-9a-f]+)?',
                          f"{asset}?v={h}", html)
        if html != original:
            p.write_text(html, encoding="utf-8")
            print(f"stamped {page}")
        else:
            print(f"{page} already current")
    for a, h in stamps.items():
        print(f"  {a} -> v={h}")


if __name__ == "__main__":
    main()
