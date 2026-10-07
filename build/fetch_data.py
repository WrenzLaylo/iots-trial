"""Snapshot their public WordPress REST API into data/ (run once, commit the output)."""
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
API = "https://www.insureonthespot.com/wp-json/wp/v2"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def get(path, **params):
    r = requests.get(f"{API}/{path}", params=params, headers=UA, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    posts = get("posts", per_page=36, _fields="id,date,link,title,excerpt,categories")
    out = [{
        "id": p["id"],
        "date": p["date"][:10],
        "link": p["link"],
        "title": p["title"]["rendered"],
        "excerpt_html": p["excerpt"]["rendered"],
        "categories": p["categories"],
    } for p in posts]
    cats = get("categories", per_page=100, _fields="id,name,slug,link,count")
    (ROOT / "data" / "posts.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    (ROOT / "data" / "categories.json").write_text(json.dumps(cats, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"posts={len(out)} categories={len(cats)} newest={out[0]['date']}")


if __name__ == "__main__":
    main()
