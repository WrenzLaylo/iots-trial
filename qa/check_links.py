"""Check every link in the built site: internal paths exist, external URLs answer 2xx/3xx."""
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


class Hrefs(HTMLParser):
    def __init__(self):
        super().__init__(); self.hrefs = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "form"):
            url = a.get("href") or a.get("action")
            if url:
                self.hrefs.add(url)


def main():
    hrefs = set()
    for f in SITE.rglob("index.html"):
        p = Hrefs(); p.feed(f.read_text(encoding="utf-8")); hrefs |= p.hrefs
    results, failures = {}, []
    for url in sorted(hrefs):
        if url.startswith(("tel:", "#", "mailto:")):
            continue
        if url.startswith("/"):
            target = SITE / url.strip("/") / "index.html" if not re.search(r"\.\w+$", url) else SITE / url.lstrip("/")
            ok = target.exists() or (SITE / url.strip("/")).is_file()
            results[url] = "ok" if ok else "missing"
        else:
            try:
                r = requests.get(url, headers=UA, timeout=30, allow_redirects=True)
                results[url] = r.status_code
                ok = r.status_code < 400
            except requests.RequestException as e:
                results[url], ok = str(e), False
            time.sleep(0.5)
        if not ok:
            failures.append(url)
    out = ROOT / "qa" / "out"; out.mkdir(parents=True, exist_ok=True)
    (out / "links.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"checked={len(results)} failures={failures}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
