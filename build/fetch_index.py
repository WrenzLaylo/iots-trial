"""Snapshot ALL posts (title, link, date, categories, word count, excerpt) for the instant-search index."""
import json
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
API = "https://www.insureonthespot.com/wp-json/wp/v2/posts"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def main():
    out, page, pages = [], 1, 1
    while page <= pages:
        r = requests.get(API, params={"per_page": 100, "page": page, "_fields": "id,date,link,title,excerpt,content,categories"},
                         headers=UA, timeout=120)
        r.raise_for_status()
        pages = int(r.headers["X-WP-TotalPages"])
        for p in r.json():
            words = len(re.sub(r"<[^>]+>", " ", p["content"]["rendered"]).split())
            out.append({"id": p["id"], "title": p["title"]["rendered"], "link": p["link"], "date": p["date"][:10],
                        "cats": p["categories"], "words": words, "excerpt_html": p["excerpt"]["rendered"]})
        page += 1
    out.sort(key=lambda p: (p["date"], p["id"]), reverse=True)
    (ROOT / "data" / "posts_index.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"posts={len(out)} newest={out[0]['date']} oldest={out[-1]['date']}")


if __name__ == "__main__":
    main()
