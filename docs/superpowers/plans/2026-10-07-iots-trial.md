# IOTS 3-Page Trial Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A noindexed, clickable static preview of insureonthespot.com's blog landing, locations and contact pages, rebuilt with the fixes in `docs/FINDINGS.md`, deployed to Vercel, with screenshots and a short note ready to submit tonight.

**Architecture:** A Python build (`build/build.py`, Jinja2) renders `templates/` + `data/` into `site/`, which is committed and served as-is by Vercel. Data (posts, categories) and assets (images, font, icons, Leaflet) are fetched once by scripts and committed, so the preview never depends on their server. Browser behaviour lives in small ES modules under `static/js/` (status pills, quote validation, menu, lazy map), unit-tested with `node:test`.

**Tech Stack:** Python 3.11 (`py -3.11`) + Jinja2 + Pillow + requests + pytest + Playwright 1.63; Node 22 (`node:test`, `axe-core`, `npx lighthouse`); Vercel CLI 48; GitHub CLI.

**Spec:** `docs/superpowers/specs/2026-10-07-iots-trial-design.md` (findings: `docs/FINDINGS.md`).

## Global Constraints

- Preview pages: `<meta name="robots" content="noindex, nofollow">` AND header `X-Robots-Tag: noindex, nofollow`; robots.txt `Allow: /` (never `Disallow`); NO `rel="canonical"`.
- JSON-LD uses production URLs (`https://www.insureonthespot.com/...`).
- Colours: navy `#005581`, dark navy `#002d45`, CTA `#ffcd3c` with `#002d45` text, page `#f6f8fa`, cards `#fff`. Status: open `#14663e` on `#e5f4ec`, closed `#8a3b12` on `#fbece3`, always with text.
- Font: Figtree, self-hosted woff2, `font-display: swap`. Body min 16px.
- Radii: cards 14px, buttons 10px, pills 999px. Tap targets min 44px.
- Icons: Phosphor regular only, inlined SVG, `aria-hidden="true"`.
- Copy we write: no em dash (`—`) or en dash (`–`) anywhere; their own post titles/excerpts are left untouched.
- Never invent facts, ratings or hours. Hours/addresses/phones only from `data/branches.json` (sourced from their branch pages).
- Holiday line, exact text: `Holiday hours may vary, call to confirm.`
- Quote URL: `https://quote.insureonthespot.com/?zipcode=NNNNN`; ZIP must match `^\d{5}$` after trimming; empty goes to `https://quote.insureonthespot.com/`.
- Title tags max 60 characters; meta descriptions 70-160 characters.
- Commits and PRs: no `Co-Authored-By` trailer and no "Generated with Claude Code" footer (Wrenz's rule).
- Every Python command uses `py -3.11`. Every task runs from repo root `C:\Users\OASIS\Downloads\vela-iots-trial`.

## Review Focus

1. **Visitor outside Chicago** (the reviewers may be in Colombia or the PH): status pills must use Chicago time, not the device's. Test: Task 7 `test_status_uses_chicago_time` (Manila timezone, fixed clock).
2. **JavaScript blocked or failing**: hours, phone links, nav links and the quote form must still work (form submits GET to the quote URL). Test: Task 7 `test_no_js_page_still_works`.
3. **Very narrow phones (320px)**: no sideways scrolling, Call buttons fit. Test: Task 7 `test_no_horizontal_overflow` includes 320px.
4. **Map tiles or Leaflet blocked**: page stays usable, Google Maps fallback link visible, no uncaught errors. Test: Task 7 `test_map_failure_is_graceful`.
5. **URL without trailing slash** (`/locations` typed by hand): must land on the page, not 404. Test: Task 8 step "trailing slash redirect" against the deployed URL.

---

## File Structure

```
build/
  fetch_data.py      # WP REST API -> data/posts.json, data/categories.json
  fetch_assets.py    # images (-> WebP), font, icons, Leaflet -> static/; writes data/images.json
  build.py           # helpers + render_all(): templates + data -> site/
  jsonld.py          # JSON-LD builders (production URLs)
data/
  branches.json      # 4 branches + 2 departments, hours, coords (hand-written from their pages)
  site.json          # every nav/footer/help URL (verified live)
  posts.json         # generated (36 posts)
  categories.json    # generated
  images.json        # generated (file -> width/height)
templates/
  base.html  _header.html  _footer.html  _macros.html
  index.html  blog.html  locations.html  contact.html
static/
  css/site.css
  js/site.js  js/hours.js  js/quote.js  js/menu.js  js/map.js
  fonts/figtree-latin.woff2        # generated
  img/*                             # generated
  icons/*.svg                       # generated (Phosphor)
  vendor/leaflet/*                  # generated
tests/
  conftest.py  test_data.py  test_helpers.py  test_site.py
  js/hours.test.mjs  js/quote.test.mjs
qa/
  serve.py  check_browser.py  check_links.py  shoot.py  lighthouse.sh
  out/                              # results, gitignored
deliverables/
  screenshots/*.png  NOTE.md
site/                               # generated output, committed, deployed
vercel.json  package.json  requirements-dev.txt
```

---

### Task 1: Data and assets foundation

**Files:**
- Create: `requirements-dev.txt`, `package.json`, `data/branches.json`, `data/site.json`, `build/fetch_data.py`, `build/fetch_assets.py`, `tests/test_data.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `data/branches.json` schema (below), `data/site.json` keys (`links`, `nav_top`, `nav_main`, `footer`), `data/posts.json` = list of `{id:int, date:"YYYY-MM-DD", link:str, title:str, excerpt_html:str, categories:[int]}`, `data/categories.json` = list of `{id, name, slug, link, count}`, `data/images.json` = `{"<file name>": [width, height]}`, `static/icons/<name>.svg`.

- [ ] **Step 1: Branch and tooling**

```bash
git checkout -b feat/foundation
py -3.11 -m pip install pytest==8.3.3
```

`requirements-dev.txt`:
```
jinja2>=3.1
pillow>=10
requests>=2.31
pytest>=8
playwright==1.63.0
```

`package.json`:
```json
{
  "name": "iots-trial",
  "private": true,
  "type": "module",
  "scripts": { "test:js": "node --test tests/js/" },
  "devDependencies": { "axe-core": "4.10.2" }
}
```

Append to `.gitignore`:
```
qa/out/
```

Run: `npm install`
Expected: `added 1 package`.

- [ ] **Step 2: Write `data/branches.json`** (values from the four live branch pages and /contact/, verified 2026-10-07; coordinates from OpenStreetMap Nominatim)

```json
{
  "timezone": "America/Chicago",
  "holiday_note": "Holiday hours may vary, call to confirm.",
  "main_phone": "773-202-5060",
  "main_tel": "+17732025060",
  "branches": [
    {"id": "hq", "name": "Corporate Headquarters", "note": "Next to the DMV (Secretary of State)",
     "street": "5485 N Elston Ave", "city": "Chicago", "state": "IL", "zip": "60630",
     "phone": "(773) 202-5060", "tel": "+17732025060", "lat": 41.98146, "lng": -87.75957,
     "url": "https://www.insureonthespot.com/locations/corporate-headquarters/",
     "hours": {"mon": ["08:00", "20:00"], "tue": ["08:00", "20:00"], "wed": ["08:00", "20:00"], "thu": ["08:00", "20:00"], "fri": ["08:00", "20:00"], "sat": ["08:00", "17:30"]}},
    {"id": "chicago-south", "name": "Chicago, IL South", "note": "",
     "street": "8537 S Cicero Ave", "city": "Chicago", "state": "IL", "zip": "60652",
     "phone": "(773) 202-0651", "tel": "+17732020651", "lat": 41.7378, "lng": -87.74085,
     "url": "https://www.insureonthespot.com/locations/chicago-il-south/",
     "hours": {"mon": ["09:30", "18:00"], "tue": ["09:30", "18:00"], "wed": ["09:30", "18:00"], "thu": ["09:30", "18:00"], "fri": ["09:30", "18:00"], "sat": ["09:00", "15:00"]}},
    {"id": "berwyn", "name": "Berwyn, IL", "note": "",
     "street": "7015 W Roosevelt Rd", "city": "Berwyn", "state": "IL", "zip": "60402",
     "phone": "(708) 857-7661", "tel": "+17088577661", "lat": 41.86474, "lng": -87.79973,
     "url": "https://www.insureonthespot.com/locations/berwyn-il/",
     "hours": {"mon": ["09:30", "18:00"], "tue": ["09:30", "18:00"], "wed": ["09:30", "18:00"], "thu": ["09:30", "18:00"], "fri": ["09:30", "18:00"], "sat": ["09:00", "15:00"]}},
    {"id": "melrose-park", "name": "Melrose Park, IL", "note": "Next to the DMV (Secretary of State)",
     "street": "1907 N Mannheim Rd", "city": "Melrose Park", "state": "IL", "zip": "60160",
     "phone": "(708) 547-1800", "tel": "+17085471800", "lat": 41.90797, "lng": -87.88367,
     "url": "https://www.insureonthespot.com/locations/melrose-park-il/",
     "hours": {"mon": ["08:00", "18:00"], "tue": ["08:00", "18:00"], "wed": ["08:00", "18:00"], "thu": ["08:00", "18:00"], "fri": ["08:00", "18:00"], "sat": ["08:00", "14:00"]}}
  ],
  "departments": [
    {"id": "customer-service", "name": "Customer Service",
     "hours": {"mon": ["08:00", "20:00"], "tue": ["08:00", "20:00"], "wed": ["08:00", "20:00"], "thu": ["08:00", "20:00"], "fri": ["08:00", "20:00"], "sat": ["08:00", "17:00"]}},
    {"id": "sales", "name": "Sales",
     "hours": {"mon": ["08:00", "20:30"], "tue": ["08:00", "20:30"], "wed": ["08:00", "20:30"], "thu": ["08:00", "20:30"], "fri": ["08:00", "20:30"], "sat": ["08:00", "17:30"]}}
  ]
}
```

- [ ] **Step 3: Write `data/site.json`** (every URL verified on the live site 2026-10-07)

```json
{
  "links": {
    "home": "https://www.insureonthespot.com/",
    "quote": "https://quote.insureonthespot.com/",
    "portal": "https://csp.insureonthespot.com/Login.aspx",
    "sr22": "https://www.insureonthespot.com/sr22-insurance/",
    "about": "https://www.insureonthespot.com/about/",
    "motorcycle": "https://www.insureonthespot.com/auto-insurance/motorcycle-insurance/",
    "customer_service": "https://www.insureonthespot.com/customer-service/",
    "payment_options": "https://www.insureonthespot.com/customer-service/payment-options/",
    "roadside": "https://www.insureonthespot.com/customer-service/roadside-assistance/",
    "claim": "https://www.insureonthespot.com/customer-service/report-insurance-claim/",
    "faq": "https://www.insureonthespot.com/customer-service/auto-insurance-faq/",
    "employment": "https://www.insureonthespot.com/employment-opportunities/",
    "service_areas": "https://www.insureonthespot.com/service-areas/",
    "location_finder": "https://www.insureonthespot.com/location-finder/",
    "ilivs": "https://www.insureonthespot.com/customer-service/ilivs-illinois-insurance-verification-system/",
    "reviews": "https://www.insureonthespot.com/see-what-our-customers-are-saying-about-us/",
    "affiliate": "https://quote.insureonthespot.com/Default.aspx/dealer",
    "privacy": "https://www.insureonthespot.com/privacy-policy/",
    "sitemap": "https://www.insureonthespot.com/sitemap/",
    "terms": "https://www.insureonthespot.com/terms-conditions/",
    "espanol": "https://www.insureonthespot.com/espanol/",
    "bbb": "https://www.bbb.org/chicago/business-reviews/auto-insurance/insure-on-the-spot-in-chicago-il-14007680/",
    "search": "https://www.insureonthespot.com/",
    "blog_older": "https://www.insureonthespot.com/customer-service/blog/page/10/",
    "gmaps_all": "https://www.google.com/maps/search/?api=1&query=Insure+On+The+Spot+Chicago+IL",
    "blog": "/customer-service/blog/",
    "locations": "/locations/",
    "contact": "/contact/"
  },
  "nav_top": [
    {"label": "Make My Payment", "key": "portal"},
    {"label": "Renew My Policy", "key": "portal"},
    {"label": "Customer Service", "key": "customer_service"},
    {"label": "Locations", "key": "locations"},
    {"label": "Contact Us", "key": "contact"}
  ],
  "nav_main": [
    {"label": "Auto Insurance", "key": "home"},
    {"label": "SR22 Insurance", "key": "sr22"},
    {"label": "About Us", "key": "about"},
    {"label": "Blog", "key": "blog"}
  ],
  "footer": [
    {"heading": "Services", "items": [
      {"label": "Auto Insurance", "key": "home"}, {"label": "SR22 Insurance", "key": "sr22"},
      {"label": "Motorcycle Insurance", "key": "motorcycle"}, {"label": "Get Free Quote", "key": "quote"},
      {"label": "Make My Payment", "key": "portal"}, {"label": "Renew My Policy", "key": "portal"}]},
    {"heading": "Locations", "items": [
      {"label": "Corporate Headquarters", "href": "https://www.insureonthespot.com/locations/corporate-headquarters/"},
      {"label": "Chicago, IL South", "href": "https://www.insureonthespot.com/locations/chicago-il-south/"},
      {"label": "Berwyn, IL", "href": "https://www.insureonthespot.com/locations/berwyn-il/"},
      {"label": "Melrose Park, IL", "href": "https://www.insureonthespot.com/locations/melrose-park-il/"},
      {"label": "Additional Areas Served", "key": "service_areas"}]},
    {"heading": "Need Help?", "items": [
      {"label": "Easy Payment Options", "key": "payment_options"}, {"label": "Report a Claim", "key": "claim"},
      {"label": "Auto Insurance FAQs", "key": "faq"}, {"label": "Tips & Resources (Articles)", "key": "blog"},
      {"label": "Contact Us", "key": "contact"}, {"label": "Employment Opportunities", "key": "employment"},
      {"label": "Location Finder", "key": "location_finder"},
      {"label": "ILIVS Illinois Insurance Verification System", "key": "ilivs"},
      {"label": "See what our customers are saying", "key": "reviews"}]}
  ],
  "legal": [
    {"label": "Affiliate Login", "key": "affiliate"}, {"label": "Privacy Policy", "key": "privacy"},
    {"label": "Sitemap", "key": "sitemap"}, {"label": "Terms & Conditions", "key": "terms"}
  ]
}
```

- [ ] **Step 4: Write the failing data tests** `tests/test_data.py`

```python
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_four_branches_with_matching_tel():
    b = load("branches.json")
    assert [x["id"] for x in b["branches"]] == ["hq", "chicago-south", "berwyn", "melrose-park"]
    for br in b["branches"]:
        digits = re.sub(r"\D", "", br["phone"])
        assert br["tel"] == "+1" + digits, br["id"]


def test_hours_are_valid_and_open_before_close():
    b = load("branches.json")
    for item in b["branches"] + b["departments"]:
        assert item["hours"], item["id"]
        for day, (opens, closes) in item["hours"].items():
            assert day in {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
            assert HHMM.match(opens) and HHMM.match(closes)
            assert opens < closes, (item["id"], day)


def test_coordinates_are_in_chicagoland():
    for br in load("branches.json")["branches"]:
        assert 41.6 < br["lat"] < 42.1 and -88.0 < br["lng"] < -87.5, br["id"]


def test_site_links_are_https_or_internal():
    links = load("site.json")["links"]
    for key, url in links.items():
        assert url.startswith("https://") or url.startswith("/"), key
    assert "http://quote" not in json.dumps(load("site.json"))


def test_nav_keys_exist():
    s = load("site.json")
    items = s["nav_top"] + s["nav_main"] + s["legal"] + [i for col in s["footer"] for i in col["items"]]
    for item in items:
        assert "href" in item or item["key"] in s["links"], item


def test_posts_snapshot():
    posts = load("posts.json")
    assert len(posts) == 36
    for p in posts:
        assert p["title"] and p["link"].startswith("https://www.insureonthespot.com/")
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", p["date"])
    dates = [p["date"] for p in posts]
    assert dates == sorted(dates, reverse=True)


def test_categories_snapshot():
    cats = load("categories.json")
    assert any(c["slug"] == "uncategorized" for c in cats)
    assert all(c["link"].startswith("https://www.insureonthespot.com/category/") for c in cats)


def test_assets_present():
    images = load("images.json")
    for name in ["logo.png", "locations-hero.webp", "contact-photo.webp", "bbb.png", "favicon.ico"]:
        assert (ROOT / "static" / "img" / name).exists(), name
        if not name.endswith(".ico"):
            assert name in images
    assert (ROOT / "static" / "fonts" / "figtree-latin.woff2").stat().st_size > 10_000
    for icon in ["phone", "navigation-arrow", "clock", "storefront", "car", "list", "x",
                 "magnifying-glass", "credit-card", "arrows-clockwise", "file-text", "truck",
                 "question", "star", "briefcase", "gift", "map-pin", "caret-right"]:
        assert (ROOT / "static" / "icons" / f"{icon}.svg").exists(), icon
    for f in ["leaflet.js", "leaflet.css", "images/marker-icon.png", "images/marker-icon-2x.png", "images/marker-shadow.png"]:
        assert (ROOT / "static" / "vendor" / "leaflet" / f).exists(), f
```

- [ ] **Step 5: Run to verify failures**

Run: `py -3.11 -m pytest tests/test_data.py -q`
Expected: first 5 PASS, `test_posts_snapshot`, `test_categories_snapshot`, `test_assets_present` FAIL (files missing).

- [ ] **Step 6: Write `build/fetch_data.py`**

```python
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
```

Note: `title` stays as rendered HTML entities (e.g. `&#038;`); `build.py` unescapes it.

- [ ] **Step 7: Write `build/fetch_assets.py`**

```python
"""Download their images (-> WebP), Figtree, Phosphor icons and Leaflet into static/."""
import io
import json
import re
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
WP = "https://www.insureonthespot.com/wp-content"

IMAGES = {
    # name: (source url, max width or None to keep as-is)
    "logo.png": (f"{WP}/themes/orbit-media/images/logo.png", None),
    "locations-hero.webp": (f"{WP}/uploads/2019/10/iots-hom-hero.jpg", 1200),
    "contact-photo.webp": (f"{WP}/uploads/2020/01/JP2_1071_web-1536x1024.jpg", 1200),
    "bbb.png": (f"{WP}/uploads/2019/12/BBBLogo.png", None),
    "favicon.ico": (f"{WP}/themes/orbit-media/favicon.ico", None),
}
ICONS = ["phone", "navigation-arrow", "clock", "storefront", "car", "list", "x", "magnifying-glass",
         "credit-card", "arrows-clockwise", "file-text", "truck", "question", "star", "briefcase",
         "gift", "map-pin", "caret-right"]
LEAFLET = "https://unpkg.com/leaflet@1.9.4/dist"
LEAFLET_FILES = ["leaflet.js", "leaflet.css", "images/marker-icon.png", "images/marker-icon-2x.png", "images/marker-shadow.png"]


def fetch(url, headers=UA):
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.content


def images():
    out = STATIC / "img"
    out.mkdir(parents=True, exist_ok=True)
    dims = {}
    for name, (url, max_w) in IMAGES.items():
        raw = fetch(url)
        if name.endswith(".webp"):
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            if max_w and im.width > max_w:
                im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
            im.save(out / name, "WEBP", quality=80, method=6)
            dims[name] = [im.width, im.height]
        else:
            (out / name).write_bytes(raw)
            if not name.endswith(".ico"):
                with Image.open(io.BytesIO(raw)) as im:
                    dims[name] = [im.width, im.height]
    (ROOT / "data" / "images.json").write_text(json.dumps(dims, indent=1), encoding="utf-8")
    print("images", dims)


def font():
    css = fetch("https://fonts.googleapis.com/css2?family=Figtree:wght@300..900&display=swap").decode()
    blocks = re.findall(r"/\* latin \*/\s*@font-face\s*{[^}]*}", css)
    url = re.search(r"url\((https://[^)]+\.woff2)\)", blocks[0]).group(1)
    (STATIC / "fonts").mkdir(parents=True, exist_ok=True)
    (STATIC / "fonts" / "figtree-latin.woff2").write_bytes(fetch(url))
    print("font", url)


def icons():
    (STATIC / "icons").mkdir(parents=True, exist_ok=True)
    for name in ICONS:
        svg = fetch(f"https://unpkg.com/@phosphor-icons/core@2.1.1/assets/regular/{name}.svg").decode()
        (STATIC / "icons" / f"{name}.svg").write_text(svg, encoding="utf-8")
    print("icons", len(ICONS))


def leaflet():
    for f in LEAFLET_FILES:
        dest = STATIC / "vendor" / "leaflet" / f
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(fetch(f"{LEAFLET}/{f}"))
    print("leaflet", len(LEAFLET_FILES))


if __name__ == "__main__":
    images(); font(); icons(); leaflet()
```

Google Fonts returns woff2 only to modern browsers; `UA` is a Chrome UA so the CSS contains woff2 URLs.

- [ ] **Step 8: Run both scripts and the tests**

Run:
```bash
py -3.11 build/fetch_data.py
py -3.11 build/fetch_assets.py
py -3.11 -m pytest tests/test_data.py -q
```
Expected: `posts=36 categories=15 newest=2026-07-05`; images/font/icons/leaflet lines; `8 passed`.

- [ ] **Step 9: Commit**

```bash
git add requirements-dev.txt package.json package-lock.json .gitignore data build tests static
git commit -m "Add data snapshot, verified site links and downloaded assets"
```

---

### Task 2: Browser logic (status, quote, menu) with unit tests

**Files:**
- Create: `static/js/hours.js`, `static/js/quote.js`, `static/js/menu.js`, `static/js/site.js`, `tests/js/hours.test.mjs`, `tests/js/quote.test.mjs`

**Interfaces:**
- Consumes: hours objects `{mon:["08:00","20:00"],...}` (Task 1 schema), emitted by templates as `data-hours` JSON.
- Produces (ES module exports):
  - `hours.js`: `DAYS` (`['sun','mon','tue','wed','thu','fri','sat']`), `chicagoNow(date?: Date, tz?: string) -> {day:0..6, minutes:int}`, `formatTime("HH:MM") -> "8 PM" | "9:30 AM"`, `statusFor(hours, now) -> {open:boolean, label:string}`, `initStatus(root?)`.
  - `quote.js`: `QUOTE_URL`, `quoteUrl(raw) -> {ok:true,url} | {ok:false,error}`, `initQuoteForms(root?)`.
  - `menu.js`: `initMenu()`. DOM contract: button `[data-menu-toggle]` with `aria-controls="site-menu"`, panel `#site-menu`.
  - `site.js`: entry module; imports the above plus `./map.js` (Task 5) dynamically.
  - DOM contract for status: `<span class="status" data-hours='{json}' hidden>`; hours rows `<div data-day="mon tue ...">`; JS sets text, `is-open`/`is-closed`, unhides, and toggles `is-today` on rows.

- [ ] **Step 1: Write failing tests** `tests/js/hours.test.mjs`

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { chicagoNow, formatTime, statusFor } from '../../static/js/hours.js';

const HQ = { mon: ['08:00', '20:00'], tue: ['08:00', '20:00'], wed: ['08:00', '20:00'], thu: ['08:00', '20:00'], fri: ['08:00', '20:00'], sat: ['08:00', '17:30'] };
const SOUTH = { mon: ['09:30', '18:00'], tue: ['09:30', '18:00'], wed: ['09:30', '18:00'], thu: ['09:30', '18:00'], fri: ['09:30', '18:00'], sat: ['09:00', '15:00'] };
const at = (day, h, m = 0) => ({ day, minutes: h * 60 + m });

test('formatTime drops :00 and uses 12-hour clock', () => {
  assert.equal(formatTime('08:00'), '8 AM');
  assert.equal(formatTime('09:30'), '9:30 AM');
  assert.equal(formatTime('17:30'), '5:30 PM');
  assert.equal(formatTime('20:30'), '8:30 PM');
  assert.equal(formatTime('12:00'), '12 PM');
  assert.equal(formatTime('00:00'), '12 AM');
});

test('open during hours', () => {
  assert.deepEqual(statusFor(HQ, at(2, 18, 30)), { open: true, label: 'Open, closes 8 PM' });
});

test('before opening today', () => {
  assert.deepEqual(statusFor(SOUTH, at(3, 7)), { open: false, label: 'Closed, opens 9:30 AM' });
});

test('exactly at closing time counts as closed', () => {
  assert.deepEqual(statusFor(HQ, at(5, 20)), { open: false, label: 'Closed, opens tomorrow 8 AM' });
});

test('Saturday after close skips Sunday', () => {
  assert.deepEqual(statusFor(HQ, at(6, 18)), { open: false, label: 'Closed, opens Monday 8 AM' });
});

test('Sunday with no published hours', () => {
  assert.deepEqual(statusFor(SOUTH, at(0, 12)), { open: false, label: 'Closed, opens tomorrow 9:30 AM' });
});

test('chicagoNow reads Chicago time across the DST change (Nov 1 2026)', () => {
  assert.deepEqual(chicagoNow(new Date('2026-10-30T13:00:00Z')), { day: 5, minutes: 480 }); // Fri 8:00 CDT
  assert.deepEqual(chicagoNow(new Date('2026-11-02T14:00:00Z')), { day: 1, minutes: 480 }); // Mon 8:00 CST
  assert.deepEqual(chicagoNow(new Date('2026-11-01T06:30:00Z')), { day: 0, minutes: 90 });  // 1:30 CDT
  assert.deepEqual(chicagoNow(new Date('2026-11-01T07:30:00Z')), { day: 0, minutes: 90 });  // 1:30 CST
});

test('midnight is minute 0, not 1440', () => {
  assert.deepEqual(chicagoNow(new Date('2026-10-07T05:00:00Z')), { day: 3, minutes: 0 }); // Wed 00:00 CDT
});
```

`tests/js/quote.test.mjs`:
```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { quoteUrl, QUOTE_URL } from '../../static/js/quote.js';

test('empty goes to the quote page without a ZIP', () => {
  assert.deepEqual(quoteUrl(''), { ok: true, url: QUOTE_URL });
  assert.deepEqual(quoteUrl('   '), { ok: true, url: QUOTE_URL });
});

test('valid ZIP, https, single parameter', () => {
  assert.deepEqual(quoteUrl('60630'), { ok: true, url: 'https://quote.insureonthespot.com/?zipcode=60630' });
  assert.deepEqual(quoteUrl(' 60630 '), { ok: true, url: 'https://quote.insureonthespot.com/?zipcode=60630' });
});

test('invalid ZIPs return an error message', () => {
  for (const bad of ['6063', '606301', 'abcde', '60630-1234', '6O630']) {
    const r = quoteUrl(bad);
    assert.equal(r.ok, false, bad);
    assert.equal(r.error, 'Enter a 5-digit ZIP code, like 60630.');
  }
});
```

- [ ] **Step 2: Run to verify failure**

Run: `npm run test:js`
Expected: FAIL, `Cannot find module .../static/js/hours.js`.

- [ ] **Step 3: Write `static/js/hours.js`**

```js
export const DAYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const toMin = (hhmm) => { const [h, m] = hhmm.split(':').map(Number); return h * 60 + m; };

export function chicagoNow(date = new Date(), tz = 'America/Chicago') {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: tz, weekday: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(date);
  const get = (type) => parts.find((p) => p.type === type).value;
  return { day: DAYS.indexOf(get('weekday').slice(0, 3).toLowerCase()), minutes: (Number(get('hour')) % 24) * 60 + Number(get('minute')) };
}

export function formatTime(hhmm) {
  const [h, m] = hhmm.split(':').map(Number);
  const suffix = h >= 12 ? 'PM' : 'AM';
  const h12 = h % 12 || 12;
  return m ? `${h12}:${String(m).padStart(2, '0')} ${suffix}` : `${h12} ${suffix}`;
}

export function statusFor(hours, now) {
  const today = hours[DAYS[now.day]];
  if (today) {
    if (now.minutes >= toMin(today[0]) && now.minutes < toMin(today[1])) {
      return { open: true, label: `Open, closes ${formatTime(today[1])}` };
    }
    if (now.minutes < toMin(today[0])) {
      return { open: false, label: `Closed, opens ${formatTime(today[0])}` };
    }
  }
  for (let i = 1; i <= 7; i += 1) {
    const d = (now.day + i) % 7;
    const h = hours[DAYS[d]];
    if (h) return { open: false, label: `Closed, opens ${i === 1 ? 'tomorrow' : DAY_NAMES[d]} ${formatTime(h[0])}` };
  }
  return { open: false, label: 'Closed' };
}

export function initStatus(root = document) {
  const pills = [...root.querySelectorAll('[data-hours]')];
  const rows = [...root.querySelectorAll('[data-day]')];
  if (!pills.length && !rows.length) return;
  const tick = () => {
    const now = chicagoNow();
    pills.forEach((el) => {
      const s = statusFor(JSON.parse(el.dataset.hours), now);
      el.textContent = s.label;
      el.classList.toggle('is-open', s.open);
      el.classList.toggle('is-closed', !s.open);
      el.hidden = false;
    });
    rows.forEach((r) => r.classList.toggle('is-today', r.dataset.day.split(' ').includes(DAYS[now.day])));
  };
  tick();
  setInterval(tick, 60_000);
}
```

- [ ] **Step 4: Write `static/js/quote.js`**

```js
export const QUOTE_URL = 'https://quote.insureonthespot.com/';
const ERROR = 'Enter a 5-digit ZIP code, like 60630.';

export function quoteUrl(raw) {
  const zip = String(raw ?? '').trim();
  if (zip === '') return { ok: true, url: QUOTE_URL };
  if (/^\d{5}$/.test(zip)) return { ok: true, url: `${QUOTE_URL}?zipcode=${zip}` };
  return { ok: false, error: ERROR };
}

export function initQuoteForms(root = document) {
  root.querySelectorAll('form[data-quote]').forEach((form) => {
    const input = form.querySelector('input[name="zipcode"]');
    const error = form.querySelector('.field-error');
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const result = quoteUrl(input.value);
      if (!result.ok) {
        error.textContent = result.error;
        error.hidden = false;
        input.setAttribute('aria-invalid', 'true');
        input.focus();
        return;
      }
      error.hidden = true;
      input.removeAttribute('aria-invalid');
      window.location.assign(result.url);
    });
  });
}
```

- [ ] **Step 5: Write `static/js/menu.js` and `static/js/site.js`**

`menu.js`:
```js
export function initMenu() {
  const button = document.querySelector('[data-menu-toggle]');
  const panel = document.getElementById('site-menu');
  if (!button || !panel) return;
  panel.hidden = true; // visible without JS, collapsed once JS runs
  const setOpen = (open) => {
    button.setAttribute('aria-expanded', String(open));
    button.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    button.querySelector('[data-icon-open]').hidden = open;
    button.querySelector('[data-icon-close]').hidden = !open;
    panel.hidden = !open;
  };
  button.addEventListener('click', () => {
    const open = button.getAttribute('aria-expanded') !== 'true';
    setOpen(open);
    if (open) panel.querySelector('a')?.focus();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && button.getAttribute('aria-expanded') === 'true') {
      setOpen(false);
      button.focus();
    }
  });
}
```

`site.js`:
```js
import { initStatus } from './hours.js';
import { initQuoteForms } from './quote.js';
import { initMenu } from './menu.js';

initMenu();
initStatus();
initQuoteForms();
if (document.querySelector('[data-map]')) {
  import('./map.js').then((m) => m.initMap()).catch(() => {});
}
```

- [ ] **Step 6: Run tests**

Run: `npm run test:js`
Expected: `# pass 11`, `# fail 0`.

- [ ] **Step 7: Commit**

```bash
git add static/js tests/js
git commit -m "Add Chicago-time status, ZIP validation and accessible menu with tests"
```

---

### Task 3: Build pipeline, shared shell, CSS, deploy config, first deploy

**Files:**
- Create: `build/build.py`, `build/jsonld.py`, `templates/base.html`, `templates/_header.html`, `templates/_footer.html`, `templates/_macros.html`, `templates/index.html`, `static/css/site.css`, `vercel.json`, `tests/conftest.py`, `tests/test_helpers.py`, `tests/test_site.py`

**Interfaces:**
- Consumes: Task 1 data files, Task 2 JS (DOM contracts above).
- Produces:
  - `build.build`: `fmt_time(hhmm)->"8:00 AM"`, `group_hours(hours)->[{label:"Mon-Fri", days:"mon tue wed thu fri", text:"8:00 AM to 8:00 PM"}]`, `clean_excerpt(html, limit=170)->str`, `directions_url(branch)->str`, `paginate(items, per_page, pages)->list[list]`, `load_context()->dict`, `render_all(out: Path) -> list[Path]` (returns written HTML files), constants `PROD`, `OUT`.
  - `build.jsonld`: `organization()`, `breadcrumbs(items: list[tuple[str,str]])`, `agency(branch)`, `blog_collection(url, posts)`, `contact_page()`.
  - Jinja globals for page templates: `links`, `nav_top`, `nav_main`, `footer`, `legal`, `icons` (name -> SVG string), `images` (name -> [w,h]), `branches`, `departments`, `holiday_note`, `main_phone`, `main_tel`, `build_id`; per page: `page = {slug, path, title, description, jsonld, crumbs}`.
  - Macros in `_macros.html`: `status(hours)`, `hours_list(rows)`, `quote_box(id, heading='h2', compact=False)`, `branch_card(b, heading='h3', compact=False)`, `crumbs(items)`.
  - `tests/conftest.py` fixture `site` (session) = path to a freshly built `site/`; helper `parse(path)->Page` with `.tags`, `.texts`, `.jsonld`, `.title`, `.html`.

- [ ] **Step 1: Write failing helper tests** `tests/test_helpers.py`

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build"))
from build import clean_excerpt, directions_url, fmt_time, group_hours, paginate  # noqa: E402

HQ = {d: ["08:00", "20:00"] for d in ["mon", "tue", "wed", "thu", "fri"]} | {"sat": ["08:00", "17:30"]}


def test_fmt_time():
    assert fmt_time("08:00") == "8:00 AM"
    assert fmt_time("20:30") == "8:30 PM"
    assert fmt_time("12:00") == "12:00 PM"


def test_group_hours_weekdays_and_saturday():
    assert group_hours(HQ) == [
        {"label": "Mon-Fri", "days": "mon tue wed thu fri", "text": "8:00 AM to 8:00 PM"},
        {"label": "Sat", "days": "sat", "text": "8:00 AM to 5:30 PM"},
    ]


def test_group_hours_gap_breaks_the_run():
    h = {"mon": ["09:00", "17:00"], "tue": ["09:00", "17:00"], "thu": ["09:00", "17:00"]}
    assert [r["label"] for r in group_hours(h)] == ["Mon-Tue", "Thu"]


def test_clean_excerpt_strips_read_more_and_entities():
    raw = ('<p class="wp-block-paragraph">Driving in Chicago can be challenging, especially when the weather '
           'gets foggy &amp; cold&hellip;&nbsp;<a class="more" href="https://x">Read More &rsaquo;</a></p>')
    assert clean_excerpt(raw) == "Driving in Chicago can be challenging, especially when the weather gets foggy & cold…"


def test_clean_excerpt_cuts_on_a_word():
    raw = "<p>" + "word " * 60 + "</p>"
    out = clean_excerpt(raw, limit=40)
    assert out.endswith("…") and len(out) <= 41 and not out[:-1].endswith(" ")


def test_directions_url():
    b = {"street": "5485 N Elston Ave", "city": "Chicago", "state": "IL", "zip": "60630"}
    assert directions_url(b) == "https://www.google.com/maps/dir/?api=1&destination=5485+N+Elston+Ave%2C+Chicago%2C+IL+60630"


def test_paginate():
    pages = paginate(list(range(36)), 12, 3)
    assert [len(p) for p in pages] == [12, 12, 12] and pages[1][0] == 12
```

Run: `py -3.11 -m pytest tests/test_helpers.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'build'`.

- [ ] **Step 2: Write `build/jsonld.py`**

```python
"""JSON-LD builders. All URLs are production URLs so the markup can move to the live site."""
PROD = "https://www.insureonthespot.com"
ORG_ID = f"{PROD}/#organization"
DAY_SCHEMA = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday",
              "fri": "Friday", "sat": "Saturday", "sun": "Sunday"}


def organization():
    return {"@context": "https://schema.org", "@type": "InsuranceAgency", "@id": ORG_ID,
            "name": "Insure On The Spot", "url": f"{PROD}/", "telephone": "+1-773-202-5060",
            "logo": f"{PROD}/wp-content/themes/orbit-media/images/logo.png", "foundingDate": "1986"}


def breadcrumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i, "name": name, "item": url}
                                for i, (name, url) in enumerate(items, start=1)]}


def opening_hours(hours):
    groups = {}
    for day, (opens, closes) in hours.items():
        groups.setdefault((opens, closes), []).append(DAY_SCHEMA[day])
    return [{"@type": "OpeningHoursSpecification", "dayOfWeek": days, "opens": o, "closes": c}
            for (o, c), days in groups.items()]


def agency(b):
    return {"@context": "https://schema.org", "@type": "InsuranceAgency", "@id": f"{b['url']}#branch",
            "name": f"Insure On The Spot, {b['name']}", "url": b["url"], "telephone": b["tel"],
            "parentOrganization": {"@id": ORG_ID},
            "address": {"@type": "PostalAddress", "streetAddress": b["street"], "addressLocality": b["city"],
                        "addressRegion": b["state"], "postalCode": b["zip"], "addressCountry": "US"},
            "geo": {"@type": "GeoCoordinates", "latitude": b["lat"], "longitude": b["lng"]},
            "openingHoursSpecification": opening_hours(b["hours"])}


def blog_collection(url, posts):
    return {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Tips & Resources",
            "url": url, "isPartOf": {"@id": f"{PROD}/#website"},
            "mainEntity": {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": i, "url": p["link"], "name": p["title"]}
                for i, p in enumerate(posts, start=1)]}}


def contact_page():
    return {"@context": "https://schema.org", "@type": "ContactPage", "url": f"{PROD}/contact/",
            "about": {"@id": ORG_ID},
            "mainEntity": {"@id": ORG_ID, "@type": "InsuranceAgency", "name": "Insure On The Spot",
                           "contactPoint": [{"@type": "ContactPoint", "telephone": "+1-773-202-5060",
                                             "contactType": "customer service", "areaServed": "US-IL",
                                             "availableLanguage": ["English", "Spanish"]}]}}
```

`availableLanguage` Spanish is supported by their Español page.

- [ ] **Step 3: Write `build/build.py`**

```python
"""Render templates + data into site/. Run: py -3.11 build/build.py"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote_plus

from jinja2 import Environment, FileSystemLoader, StrictUndefined

import jsonld

ROOT = Path(__file__).resolve().parent.parent
DATA, TPL, STATIC, OUT = ROOT / "data", ROOT / "templates", ROOT / "static", ROOT / "site"
PROD = jsonld.PROD
DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DAY_ABBR = {"mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu", "fri": "Fri", "sat": "Sat", "sun": "Sun"}
PER_PAGE, BLOG_PAGES = 12, 3
HIDDEN_CATEGORIES = {"uncategorized"}


def fmt_time(hhmm: str) -> str:
    h, m = map(int, hhmm.split(":"))
    return f"{h % 12 or 12}:{m:02d} {'PM' if h >= 12 else 'AM'}"


def _row(days, span):
    label = DAY_ABBR[days[0]] if len(days) == 1 else f"{DAY_ABBR[days[0]]}-{DAY_ABBR[days[-1]]}"
    return {"label": label, "days": " ".join(days), "text": f"{fmt_time(span[0])} to {fmt_time(span[1])}"}


def group_hours(hours: dict) -> list[dict]:
    rows, run = [], []
    for day in DAY_KEYS:
        span = hours.get(day)
        if span and run and hours[run[-1]] == span:
            run.append(day)
            continue
        if run:
            rows.append(_row(run, hours[run[0]]))
        run = [day] if span else []
    if run:
        rows.append(_row(run, hours[run[0]]))
    return rows


def clean_excerpt(raw: str, limit: int = 170) -> str:
    text = re.sub(r"<a\b[^>]*>.*?</a>", " ", raw, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text)).replace("\xa0", " ")
    text = re.sub(r"\[(?:…|\.\.\.)\]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    truncated = text.endswith("…") or text.endswith("...")
    text = text.rstrip("…").rstrip(".").rstrip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(",;:")
        truncated = True
    return text + ("…" if truncated else "")


def directions_url(b: dict) -> str:
    return "https://www.google.com/maps/dir/?api=1&destination=" + quote_plus(f"{b['street']}, {b['city']}, {b['state']} {b['zip']}")


def paginate(items: list, per_page: int, pages: int) -> list[list]:
    return [items[i * per_page:(i + 1) * per_page] for i in range(pages)]


def _json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _icons() -> dict:
    out = {}
    for svg in (STATIC / "icons").glob("*.svg"):
        body = svg.read_text(encoding="utf-8")
        body = re.sub(r'\s(width|height)="[^"]*"', "", body)
        body = body.replace('fill="#000000"', 'fill="currentColor"')
        body = body.replace("<svg ", '<svg class="icon" aria-hidden="true" focusable="false" ', 1)
        out[svg.stem] = body
    return out


def load_context() -> dict:
    site, br = _json("site.json"), _json("branches.json")
    links = site["links"]
    resolve = lambda items: [{"label": i["label"], "href": i.get("href") or links[i["key"]]} for i in items]
    branches = [b | {"hours_rows": group_hours(b["hours"]), "directions": directions_url(b)} for b in br["branches"]]
    departments = [d | {"hours_rows": group_hours(d["hours"])} for d in br["departments"]]
    try:
        build_id = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        build_id = "dev"
    return {
        "links": links, "nav_top": resolve(site["nav_top"]), "nav_main": resolve(site["nav_main"]),
        "footer": [{"heading": c["heading"], "items": resolve(c["items"])} for c in site["footer"]],
        "legal": resolve(site["legal"]), "icons": _icons(), "images": _json("images.json"),
        "branches": branches, "departments": departments, "holiday_note": br["holiday_note"],
        "main_phone": br["main_phone"], "main_tel": br["main_tel"], "build_id": build_id,
    }


def _env() -> Environment:
    return Environment(loader=FileSystemLoader(TPL), autoescape=True, undefined=StrictUndefined,
                       trim_blocks=True, lstrip_blocks=True)


def _write(out: Path, rel: str, content: str) -> Path:
    path = out / rel / "index.html" if rel else out / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def pages(ctx: dict) -> list[tuple[str, str, dict]]:
    """(template, output dir relative to site/, page dict). Extended by Tasks 4-6."""
    return [("index.html", "", {"slug": "home", "path": "/", "title": "Insure On The Spot preview: 3 rebuilt pages",
                                "description": "Trial task preview for Vela: rebuilt blog, locations and contact pages for Insure On The Spot, with an audit of what was fixed and why.",
                                "jsonld": [], "crumbs": []})]


def render_all(out: Path = OUT) -> list[Path]:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(STATIC, out / "assets", ignore=shutil.ignore_patterns("icons"))
    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    ctx, env = load_context(), _env()
    written = []
    for template, rel, page in pages(ctx):
        extra = page.pop("extra", {})
        html_out = env.get_template(template).render(**ctx, **extra, page=page)
        written.append(_write(out, rel, html_out))
    return written


if __name__ == "__main__":
    for p in render_all():
        print(p.relative_to(ROOT))
```

Run: `py -3.11 -m pytest tests/test_helpers.py -q`
Expected: `7 passed`.

- [ ] **Step 4: Write templates**

`templates/_macros.html`:
```jinja
{% macro status(hours) %}<span class="status" data-hours='{{ hours | tojson }}' hidden></span>{% endmacro %}

{% macro hours_list(rows) %}
<dl class="hours">
{% for r in rows %}<div data-day="{{ r.days }}"><dt>{{ r.label }}</dt><dd>{{ r.text }}</dd></div>{% endfor %}
</dl>
{% endmacro %}

{% macro crumbs(items) %}
<nav class="crumbs" aria-label="Breadcrumb"><ol>
{% for label, href in items %}<li>{% if loop.last %}<span aria-current="page">{{ label }}</span>{% else %}<a href="{{ href }}">{{ label }}</a>{% endif %}</li>{% endfor %}
</ol></nav>
{% endmacro %}

{% macro quote_box(id, heading='h2', compact=False) %}
<section class="quote-box{% if compact %} is-compact{% endif %}" aria-labelledby="quote-h-{{ id }}">
  <{{ heading }} id="quote-h-{{ id }}">Get a free auto insurance quote</{{ heading }}>
  {% if not compact %}<ul class="perks"><li>Lowest rates in Chicagoland</li><li>We shop, you save</li><li>SR22s filed electronically</li></ul>{% endif %}
  <form action="{{ links.quote }}" method="get" data-quote novalidate>
    <label for="zip-{{ id }}">ZIP code</label>
    <div class="quote-row">
      <input id="zip-{{ id }}" name="zipcode" type="text" inputmode="numeric" autocomplete="postal-code" maxlength="10" aria-describedby="zip-err-{{ id }}">
      <button class="btn btn-cta" type="submit">Get Free Quote</button>
    </div>
    <p class="field-error" id="zip-err-{{ id }}" role="alert" hidden></p>
  </form>
</section>
{% endmacro %}

{% macro branch_card(b, heading='h3', compact=False) %}
<article class="card branch" id="{{ b.id }}">
  <div class="branch-head">
    <div>
      <{{ heading }}>{{ b.name }}</{{ heading }}>
      {% if b.note %}<p class="note">{{ b.note }}</p>{% endif %}
    </div>
    {{ status(b.hours) }}
  </div>
  <address>{{ b.street }}, {{ b.city }}, {{ b.state }} {{ b.zip }}</address>
  {% if not compact %}
  {{ hours_list(b.hours_rows) }}
  <p class="holiday">{{ holiday_note }}</p>
  {% endif %}
  <div class="actions">
    <a class="btn btn-primary call-btn" href="tel:{{ b.tel }}">{{ icons.phone | safe }}<span>Call {{ b.phone }}<span class="visually-hidden"> ({{ b.name }})</span></span></a>
    <span class="link-row">
      <a href="{{ b.directions }}" target="_blank" rel="noopener">{{ icons['navigation-arrow'] | safe }}Directions<span class="visually-hidden"> to {{ b.name }}, opens Google Maps</span></a>
      {% if not compact %}<a href="{{ b.url }}">Branch details<span class="visually-hidden">: {{ b.name }}</span></a>{% endif %}
    </span>
  </div>
</article>
{% endmacro %}
```

`templates/base.html`:
```jinja
<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{{ page.title }}</title>
<meta name="description" content="{{ page.description }}">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#002d45">
<link rel="icon" href="/assets/img/favicon.ico">
<link rel="preload" href="/assets/fonts/figtree-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css?v={{ build_id }}">
<script>document.documentElement.classList.replace('no-js', 'js');</script>
<script type="module" src="/assets/js/site.js?v={{ build_id }}"></script>
{% for block in page.jsonld %}<script type="application/ld+json">{{ block | tojson }}</script>
{% endfor %}
</head>
<body class="page-{{ page.slug }}">
<a class="skip-link" href="#main">Skip to main content</a>
{% include "_header.html" %}
<main id="main" tabindex="-1">
{% block main %}{% endblock %}
</main>
{% include "_footer.html" %}
</body>
</html>
```

`templates/_header.html`:
```jinja
<div class="topbar">
  <div class="wrap">
    <p class="topbar-left"><a class="topbar-call" href="tel:{{ main_tel }}">{{ icons.phone | safe }}Call now {{ main_phone }}</a><span aria-hidden="true">|</span><a href="{{ links.espanol }}" lang="es" hreflang="es">Español</a></p>
    <ul>{% for l in nav_top %}<li><a href="{{ l.href }}"{% if l.href == page.path %} aria-current="page"{% endif %}>{{ l.label }}</a></li>{% endfor %}</ul>
  </div>
</div>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/"><img src="/assets/img/logo.png" alt="Insure On The Spot, preview home" width="{{ images['logo.png'][0] }}" height="{{ images['logo.png'][1] }}"></a>
    <nav class="main-nav" aria-label="Main">
      <ul>
        {% for l in nav_main %}<li><a href="{{ l.href }}"{% if page.path.startswith(l.href) and l.href.startswith('/') %} aria-current="page"{% endif %}>{{ l.label }}</a></li>{% endfor %}
        <li><a class="btn btn-cta" href="{{ links.quote }}">Get Free Quote</a></li>
      </ul>
    </nav>
    <div class="header-actions">
      <a class="icon-btn icon-btn-call" href="tel:{{ main_tel }}" aria-label="Call {{ main_phone }}">{{ icons.phone | safe }}</a>
      <button class="icon-btn" type="button" data-menu-toggle aria-controls="site-menu" aria-expanded="false" aria-label="Open menu"><span data-icon-open>{{ icons.list | safe }}</span><span data-icon-close hidden>{{ icons.x | safe }}</span></button>
    </div>
  </div>
  <nav id="site-menu" class="mobile-menu" aria-label="Menu">
    <ul>
      {% for l in nav_main %}<li><a href="{{ l.href }}">{{ l.label }}</a></li>{% endfor %}
      <li><a href="{{ links.locations }}">Locations</a></li>
      <li><a href="{{ links.contact }}">Contact Us</a></li>
      <li><a href="{{ links.customer_service }}">Customer Service</a></li>
      <li><a href="{{ links.portal }}">Make My Payment</a></li>
      <li><a href="{{ links.portal }}">Renew My Policy</a></li>
      <li><a href="{{ links.espanol }}" lang="es" hreflang="es">Español</a></li>
      <li class="menu-cta"><a class="btn btn-cta" href="{{ links.quote }}">Get Free Quote</a></li>
    </ul>
  </nav>
</header>
```

`templates/_footer.html`:
```jinja
{% from "_macros.html" import quote_box %}
<footer class="site-footer">
  <div class="wrap footer-grid">
    {% for col in footer %}
    <div>
      <h2>{{ col.heading }}</h2>
      <ul>{% for l in col.items %}<li><a href="{{ l.href }}">{{ l.label }}</a></li>{% endfor %}</ul>
      {% if col.heading == "Services" %}<p class="footer-call"><a href="tel:{{ main_tel }}">Call now {{ main_phone }}</a></p>{% endif %}
    </div>
    {% endfor %}
    <div class="footer-quote">
      {{ quote_box('footer', heading='h2', compact=True) }}
      <a class="bbb" href="{{ links.bbb }}"><img src="/assets/img/bbb.png" alt="BBB Accredited Business, view Insure On The Spot on BBB" width="{{ images['bbb.png'][0] }}" height="{{ images['bbb.png'][1] }}" loading="lazy"></a>
    </div>
  </div>
  <div class="wrap footer-bottom">
    <ul>{% for l in legal %}<li><a href="{{ l.href }}">{{ l.label }}</a></li>{% endfor %}</ul>
    <p>Copyright © 2026 Insure On The Spot. Trusted since 1986.</p>
  </div>
</footer>
```

`templates/index.html`:
```jinja
{% extends "base.html" %}
{% block main %}
<section class="wrap index-intro">
  <h1>Insure On The Spot: three rebuilt pages</h1>
  <p class="lede">A preview built for Vela's trial task. It is not indexed by search engines. Content, branches and hours come from the live insureonthespot.com.</p>
  <ul class="index-links">
    <li><a class="card" href="/customer-service/blog/"><strong>Tips &amp; Resources</strong><span>Blog landing page</span></a></li>
    <li><a class="card" href="/locations/"><strong>Our Locations</strong><span>4 offices, hours, map</span></a></li>
    <li><a class="card" href="/contact/"><strong>Contact Us</strong><span>Phone, hours, branches</span></a></li>
  </ul>
</section>
{% endblock %}
```

Index links are only added in Tasks 4-6 as each page exists; until then they 404 locally, which is fine on this branch.

- [ ] **Step 5: Write `static/css/site.css`** (full file)

```css
@font-face{font-family:"Figtree";src:url("/assets/fonts/figtree-latin.woff2") format("woff2");font-weight:300 900;font-style:normal;font-display:swap}
:root{
  --navy:#005581;--navy-dark:#002d45;--ink:#1e2b36;--ink-2:#3d4d5a;--muted:#5b6b78;
  --line:#e3e8ee;--line-2:#c9d5df;--bg:#f6f8fa;--surface:#fff;
  --cta:#ffcd3c;--cta-hover:#ffc21a;--cta-ink:#002d45;
  --open-ink:#14663e;--open-bg:#e5f4ec;--closed-ink:#8a3b12;--closed-bg:#fbece3;
  --promo-bg:#fff8e1;--promo-line:#f3dc8c;--focus:#1a73e8;
  --r-card:14px;--r-btn:10px;--shadow:0 1px 2px rgba(0,45,69,.06);
  --wrap:1200px;--gutter:clamp(16px,4vw,32px);
  --safe-l:env(safe-area-inset-left,0px);--safe-r:env(safe-area-inset-right,0px);--safe-b:env(safe-area-inset-bottom,0px);
}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-padding-top:88px}
body{margin:0;font:400 16px/1.6 "Figtree",system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:var(--bg)}
img{max-width:100%;height:auto;display:block}
a{color:var(--navy);text-underline-offset:2px}
a:hover{color:var(--navy-dark)}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px;border-radius:4px}
main:focus{outline:none}
h1,h2,h3{color:var(--navy-dark);line-height:1.15;margin:0 0 .45em}
h1{font-size:clamp(28px,4vw,40px);font-weight:800;letter-spacing:-.015em}
h2{font-size:clamp(20px,2.4vw,26px);font-weight:700}
h3{font-size:18px;font-weight:700}
p{margin:0 0 1em}
address{font-style:normal}
.wrap{max-width:var(--wrap);margin:0 auto;padding-left:calc(var(--gutter) + var(--safe-l));padding-right:calc(var(--gutter) + var(--safe-r))}
.skip-link{position:absolute;left:8px;top:-80px;z-index:100;background:var(--navy-dark);color:#fff;padding:10px 14px;border-radius:8px}
.skip-link:focus{top:8px;color:#fff}
.visually-hidden{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap}
.icon{width:1.15em;height:1.15em;flex:none;fill:currentColor;vertical-align:-.2em}
.section{padding-block:28px}
.section-title{margin-bottom:14px}

/* buttons and links */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:10px 16px;border-radius:var(--r-btn);border:1px solid transparent;font:700 15px/1.2 inherit;text-decoration:none;cursor:pointer;white-space:nowrap;transition:background-color .15s ease,transform .1s ease}
.btn:active{transform:translateY(1px)}
.btn-cta{background:var(--cta);color:var(--cta-ink)}
.btn-cta:hover{background:var(--cta-hover);color:var(--cta-ink)}
.btn-primary{background:var(--navy);color:#fff}
.btn-primary:hover{background:var(--navy-dark);color:#fff}
.link-row{display:inline-flex;flex-wrap:wrap;gap:0 18px}
.link-row a{display:inline-flex;align-items:center;gap:5px;min-height:44px;font-weight:600;text-decoration:none}
.link-row a:hover{text-decoration:underline}

/* header */
.topbar{background:var(--navy-dark);color:#dbe7ef;font-size:13.5px;font-weight:500}
.topbar .wrap{display:flex;justify-content:space-between;align-items:center;gap:16px;min-height:36px}
.topbar a{color:#dbe7ef;text-decoration:none}
.topbar a:hover{color:#fff;text-decoration:underline}
.topbar-left{display:flex;align-items:center;gap:10px;margin:0}
.topbar .topbar-call{color:var(--cta);font-weight:700;display:inline-flex;align-items:center;gap:6px}
.topbar ul{display:flex;gap:20px;list-style:none;margin:0;padding:0}
.site-header{position:sticky;top:0;z-index:50;background:#fff;border-bottom:1px solid var(--line);padding-top:env(safe-area-inset-top,0px)}
.site-header>.wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:72px}
.brand img{height:42px;width:auto}
.main-nav ul{display:flex;align-items:center;gap:24px;list-style:none;margin:0;padding:0}
.main-nav a:not(.btn){color:var(--navy-dark);font-weight:600;font-size:16px;text-decoration:none}
.main-nav a:not(.btn):hover,.main-nav a[aria-current="page"]{color:var(--navy);text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:8px}
.header-actions{display:none;gap:8px}
.icon-btn{width:44px;height:44px;display:inline-grid;place-items:center;border-radius:12px;border:1px solid var(--line-2);background:#fff;color:var(--navy-dark);cursor:pointer;padding:0}
.icon-btn .icon{width:22px;height:22px;vertical-align:0}
.icon-btn-call{background:var(--cta);border-color:var(--cta)}
.mobile-menu ul{list-style:none;margin:0;padding:4px var(--gutter) 16px}
.mobile-menu a:not(.btn){display:flex;align-items:center;min-height:48px;color:var(--navy-dark);font-weight:600;text-decoration:none;border-bottom:1px solid var(--line)}
.mobile-menu .menu-cta{padding-top:12px}
.mobile-menu .menu-cta .btn{width:100%}
@media (min-width:1024px){.mobile-menu{display:none}}
@media (max-width:1023px){
  .topbar,.main-nav{display:none}
  .header-actions{display:flex}
  .site-header>.wrap{min-height:60px}
  .brand img{height:32px}
  .mobile-menu{border-top:1px solid var(--line);max-height:calc(100dvh - 60px);overflow-y:auto}
}

/* page head */
.page-head{background:#fff;border-bottom:1px solid var(--line)}
.page-head-grid{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);align-items:stretch}
.page-head-text{padding:30px 32px 30px 0}
.page-head-photo{position:relative;min-height:240px}
.page-head-photo img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:70% 30%}
.eyebrow{font-weight:700;color:var(--navy);margin:0 0 6px}
.crumbs{font-size:13.5px;color:var(--muted);margin-bottom:8px}
.crumbs ol{display:flex;flex-wrap:wrap;gap:6px;list-style:none;margin:0;padding:0}
.crumbs li+li::before{content:"/";margin-right:6px}
.lede{font-size:17px;color:var(--ink-2);max-width:56ch}
.facts{display:flex;flex-wrap:wrap;gap:6px 20px;list-style:none;margin:0;padding:0;font-weight:600;color:var(--navy-dark);font-size:15px}
.facts li{display:inline-flex;align-items:center;gap:6px}
.facts .icon{color:var(--navy)}
@media (max-width:767px){
  .page-head-grid{grid-template-columns:1fr}
  .page-head-text{padding:18px 0 14px}
  .page-head-photo{display:none}
}

/* cards, status, hours */
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-card);box-shadow:var(--shadow);padding:18px}
.status{display:inline-flex;align-items:center;font-size:13px;font-weight:700;border-radius:999px;padding:4px 10px;white-space:nowrap;background:#eef2f5;color:var(--ink-2)}
.status.is-open{background:var(--open-bg);color:var(--open-ink)}
.status.is-closed{background:var(--closed-bg);color:var(--closed-ink)}
.status[hidden]{display:none}
.hours{display:grid;grid-template-columns:max-content 1fr;gap:2px 14px;margin:10px 0 0;font-size:15px;color:var(--ink-2)}
.hours div{display:contents}
.hours dt,.hours dd{margin:0}
.hours .is-today dt,.hours .is-today dd{font-weight:700;color:var(--navy-dark)}
.holiday{font-size:13.5px;color:var(--muted);margin:6px 0 0}

/* branch cards */
.branch-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.branch h2,.branch h3{margin:0}
.branch .note{font-size:14px;color:var(--muted);margin:2px 0 0}
.branch address{margin-top:10px}
.branch .actions{display:flex;flex-wrap:wrap;align-items:center;gap:6px 18px;margin-top:12px}
@media (max-width:767px){
  .branch .call-btn{width:100%;min-height:48px}
  .branch-head{flex-wrap:wrap}
}

/* locations */
.loc-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:22px;align-items:start}
.branch-list{display:grid;gap:14px;list-style:none;margin:0;padding:0}
.map-panel{position:sticky;top:88px}
.map-canvas{height:540px;border-radius:var(--r-card);border:1px solid var(--line);background:#e8edf1}
.map-panel .link-row{margin-top:4px}
@media (max-width:1023px){
  .loc-layout{grid-template-columns:1fr}
  .map-panel{position:static}
  .map-canvas{height:320px}
}
.leaflet-container{font:inherit}

/* quote box and promo */
.quote-box{background:var(--navy-dark);color:#fff;border-radius:var(--r-card);padding:22px}
.quote-box h2,.quote-box h3{color:#fff;font-size:21px}
.quote-box .perks{margin:0 0 14px;padding-left:20px;color:#dbe7ef}
.quote-box label{display:block;font-weight:600;margin-bottom:6px}
.quote-row{display:flex;flex-wrap:wrap;gap:8px}
.quote-row input{flex:1 1 150px;min-width:0;min-height:48px;border-radius:var(--r-btn);border:1px solid #9fb4c3;padding:10px 12px;font:inherit;font-size:16px;color:var(--ink);background:#fff}
.quote-row .btn{flex:0 0 auto;min-height:48px}
.field-error{color:#ffd9d4;font-weight:600;margin:8px 0 0}
.quote-box.is-compact{background:transparent;padding:0}
.promo{background:var(--promo-bg);border:1px solid var(--promo-line);border-radius:var(--r-card);padding:18px 20px}
.promo h2,.promo h3{font-size:19px;margin-bottom:4px}
.promo p{margin:0;color:var(--ink-2)}
.after-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:22px;align-items:start}
@media (max-width:767px){.after-grid{grid-template-columns:1fr}}

/* blog */
.blog-layout{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:28px;align-items:start}
.blog-tools{display:grid;gap:14px;margin-bottom:20px}
.search{display:flex;gap:8px;max-width:520px}
.search input{flex:1;min-width:0;min-height:48px;border-radius:var(--r-btn);border:1px solid var(--line-2);padding:10px 12px;font:inherit;font-size:16px}
.chips{display:flex;gap:8px;list-style:none;margin:0;padding:2px 2px 10px;overflow-x:auto;scroll-snap-type:x proximity}
.chips li{scroll-snap-align:start}
.chips a{display:inline-flex;align-items:center;min-height:44px;padding:8px 16px;border-radius:999px;background:#fff;border:1px solid var(--line-2);color:var(--navy-dark);font-weight:600;font-size:14.5px;white-space:nowrap;text-decoration:none}
.chips a:hover{border-color:var(--navy);color:var(--navy)}
.post-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;list-style:none;margin:0;padding:0}
.post{position:relative;height:100%;display:flex;flex-direction:column;gap:8px;transition:border-color .15s ease}
.post:hover{border-color:var(--navy)}
.post:focus-within{outline:3px solid var(--focus);outline-offset:2px}
.post .meta{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:13.5px;color:var(--muted);font-weight:600}
.post .topic{color:var(--navy)}
.post-title{font-size:19px;margin:0}
.post-title a{color:var(--navy-dark);text-decoration:none}
.post-title a::after{content:"";position:absolute;inset:0;border-radius:var(--r-card)}
.post-title a:focus-visible{outline:none}
.post p{margin:0;color:var(--ink-2);font-size:15.5px}
.post .more{margin-top:auto;font-weight:700;color:var(--navy);display:inline-flex;align-items:center;gap:4px}
.post-featured{grid-column:1/-1;padding:24px}
.post-featured .post-title{font-size:clamp(22px,2.6vw,28px)}
.quote-inline{display:none}
.blog-side{display:grid;gap:18px;position:sticky;top:88px}
.help-list{list-style:none;margin:0;padding:0}
.help-list a{display:flex;align-items:center;gap:10px;min-height:44px;font-weight:600;text-decoration:none;color:var(--navy-dark)}
.help-list a:hover{color:var(--navy);text-decoration:underline}
.pagination{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:24px;list-style:none;padding:0}
.pagination a,.pagination span{min-width:44px;min-height:44px;display:inline-flex;align-items:center;justify-content:center;padding:0 14px;border-radius:var(--r-btn);border:1px solid var(--line-2);background:#fff;font-weight:700;text-decoration:none}
.pagination [aria-current="page"]{background:var(--navy);border-color:var(--navy);color:#fff}
@media (max-width:1023px){
  .blog-layout{grid-template-columns:1fr}
  .blog-side{position:static}
  .blog-side .quote-box{display:none}
  .quote-inline{display:block;grid-column:1/-1}
}
@media (max-width:767px){.post-grid{grid-template-columns:1fr}}

/* contact */
.contact-grid{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,.75fr);gap:24px;align-items:start}
.big-phone{display:inline-flex;align-items:center;gap:10px;min-height:44px;font-size:clamp(26px,4vw,34px);font-weight:800;color:var(--navy-dark);text-decoration:none}
.big-phone .icon{color:var(--navy)}
.dept-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:14px}
.dept h3{margin:0}
.dept .branch-head{margin-bottom:4px}
.tasks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;list-style:none;margin:0;padding:0}
.tasks a{display:flex;align-items:center;gap:12px;min-height:60px;padding:14px 16px;background:#fff;border:1px solid var(--line);border-radius:var(--r-card);font-weight:700;color:var(--navy-dark);text-decoration:none}
.tasks a:hover{border-color:var(--navy);color:var(--navy)}
.tasks .icon{width:24px;height:24px;color:var(--navy)}
.branch-mini{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;list-style:none;margin:0;padding:0}
.contact-side{display:grid;gap:18px}
.trust{display:flex;flex-wrap:wrap;align-items:center;gap:14px}
.trust img{height:56px;width:auto}
@media (max-width:1023px){.contact-grid{grid-template-columns:1fr}}
@media (max-width:767px){.dept-grid,.tasks,.branch-mini{grid-template-columns:1fr}}

/* index */
.index-intro{padding-block:40px}
.index-links{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;list-style:none;margin:20px 0 0;padding:0}
.index-links a{display:flex;flex-direction:column;gap:4px;text-decoration:none;color:var(--ink-2)}
.index-links strong{color:var(--navy-dark);font-size:19px}

/* footer */
.site-footer{background:var(--navy-dark);color:#c6d6e0;margin-top:40px;padding-bottom:calc(20px + var(--safe-b))}
.footer-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr)) minmax(0,1.3fr);gap:28px;padding-top:40px;padding-bottom:26px}
.site-footer h2{color:#fff;font-size:18px}
.site-footer ul{list-style:none;margin:0;padding:0}
.site-footer a{color:#dbe7ef;text-decoration:none;display:inline-flex;align-items:center;min-height:36px}
.site-footer a:hover{color:#fff;text-decoration:underline}
.footer-call a{color:var(--cta);font-weight:700}
.footer-quote{display:grid;gap:16px;align-content:start}
.bbb img{height:56px;width:auto;background:#fff;border-radius:8px;padding:4px}
.footer-bottom{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px 20px;border-top:1px solid rgba(255,255,255,.14);padding-top:14px;font-size:13.5px}
.footer-bottom ul{display:flex;flex-wrap:wrap;gap:0 18px}
.footer-bottom p{margin:0;display:flex;align-items:center}
@media (max-width:1023px){.footer-grid{grid-template-columns:1fr 1fr}}
@media (max-width:599px){.footer-grid{grid-template-columns:1fr}.site-footer a{min-height:44px}}

@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
```

- [ ] **Step 6: Write `vercel.json`**

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": null,
  "installCommand": "echo skip",
  "buildCommand": "echo static",
  "outputDirectory": "site",
  "trailingSlash": true,
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Robots-Tag", "value": "noindex, nofollow" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

- [ ] **Step 7: Write site tests** `tests/conftest.py`

```python
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build"))


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.html, self.tags, self.jsonld, self._capture, self.title, self.texts = html, [], [], None, "", {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "title" or (tag == "script" and a.get("type") == "application/ld+json") or tag in ("h1",):
            self._capture = [tag, ""]

    def handle_data(self, data):
        if self._capture:
            self._capture[1] += data

    def handle_endtag(self, tag):
        if self._capture and tag == self._capture[0]:
            if tag == "title":
                self.title = self._capture[1].strip()
            elif tag == "script":
                self.jsonld.append(json.loads(self._capture[1]))
            else:
                self.texts.setdefault(tag, []).append(self._capture[1].strip())
            self._capture = None

    def find(self, tag, **attrs):
        return [a for t, a in self.tags if t == tag and all(a.get(k.replace("_", "-")) == v for k, v in attrs.items())]


@pytest.fixture(scope="session")
def site(tmp_path_factory):
    from build import render_all
    out = tmp_path_factory.mktemp("site")
    render_all(out)
    return out


def parse(site: Path, rel: str) -> Page:
    path = site / rel.strip("/") / "index.html" if rel.strip("/") else site / "index.html"
    return Page(path.read_text(encoding="utf-8"))
```

`tests/test_site.py`:
```python
import json
import re
from pathlib import Path

import pytest

from conftest import ROOT, parse

PAGES = ["/"]  # Tasks 4-6 extend this list


@pytest.mark.parametrize("rel", PAGES)
def test_head_rules(site, rel):
    p = parse(site, rel)
    assert len(p.texts.get("h1", [])) == 1
    assert 10 <= len(p.title) <= 60, p.title
    desc = p.find("meta", name="description")[0]["content"]
    assert 70 <= len(desc) <= 160, len(desc)
    assert p.find("meta", name="robots")[0]["content"] == "noindex, nofollow"
    assert not p.find("link", rel="canonical")
    assert p.find("html")[0]["lang"] == "en"
    assert p.find("a", **{"class": "skip-link"})[0]["href"] == "#main"
    for block in p.jsonld:
        assert block["@context"] == "https://schema.org"


@pytest.mark.parametrize("rel", PAGES)
def test_images_have_alt_and_size(site, rel):
    p = parse(site, rel)
    for _, a in [t for t in p.tags if t[0] == "img"]:
        assert a.get("alt"), a
        assert a.get("width") and a.get("height"), a


@pytest.mark.parametrize("rel", PAGES)
def test_links_are_safe(site, rel):
    p = parse(site, rel)
    assert "http://quote" not in p.html
    es = [a for t, a in p.tags if t == "a" and a.get("hreflang") == "es"]
    assert es and all(a.get("lang") == "es" for a in es)
    tels = {a["href"] for t, a in p.tags if t == "a" and a.get("href", "").startswith("tel:")}
    allowed = {"tel:+17732025060", "tel:+17732020651", "tel:+17088577661", "tel:+17085471800"}
    assert tels <= allowed, tels - allowed


def test_robots_txt_is_open(site):
    assert (site / "robots.txt").read_text() == "User-agent: *\nAllow: /\n"


def test_vercel_headers_noindex():
    cfg = json.loads((ROOT / "vercel.json").read_text())
    headers = {h["key"]: h["value"] for h in cfg["headers"][0]["headers"]}
    assert headers["X-Robots-Tag"] == "noindex, nofollow" and cfg["outputDirectory"] == "site"


def test_our_copy_has_no_long_dashes():
    files = list((ROOT / "templates").glob("*.html")) + [ROOT / "data" / "site.json", ROOT / "data" / "branches.json"]
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert "—" not in text and "–" not in text, f.name
```

- [ ] **Step 8: Build and run all tests**

Run:
```bash
py -3.11 build/build.py
py -3.11 -m pytest -q
npm run test:js
```
Expected: `site\index.html`; pytest all pass (`17 passed` or more); JS `# pass 11`.

- [ ] **Step 9: Quick visual check of the shell**

Run: `py -3.11 -m http.server 8080 --directory site` (background), open `http://localhost:8080/` at 1440px and 393px (Playwright screenshot or browser). Check: top bar, header, footer render in Figtree; mobile shows Call + menu buttons; menu opens/closes, Esc closes and returns focus. Stop the server by its own PID only (never by process name).

- [ ] **Step 10: GitHub repo, first PR, Vercel project**

```bash
git add build templates static/css vercel.json tests site
git commit -m "Add build pipeline, shared header/footer, CSS and Vercel config"
gh repo create WrenzLaylo/iots-trial --private --source . --remote origin
git push -u origin main
git push -u origin feat/foundation
gh pr create --base main --head feat/foundation --title "Foundation: data, assets, build pipeline, shared shell" --body "Data snapshot from their REST API, verified links, assets, Chicago-time status logic, ZIP validation, accessible menu, header/footer, CSS, noindex config. Tests: pytest + node:test. Spec: docs/superpowers/specs/2026-10-07-iots-trial-design.md"
vercel link --yes --project iots-trial
vercel deploy
```
Expected: PR URL; a preview URL from `vercel deploy`. Record both in the task log.

---

### Task 4: Blog page (pages 1-3)

**Files:**
- Create: `templates/blog.html`
- Modify: `build/build.py` (`pages()`), `tests/test_site.py` (`PAGES`, blog tests)

**Interfaces:**
- Consumes: `paginate`, `clean_excerpt`, `jsonld.blog_collection`, `jsonld.breadcrumbs`, macros `quote_box`, `crumbs`; data `posts.json`, `categories.json`.
- Produces: `site/customer-service/blog/index.html`, `.../page/2/index.html`, `.../page/3/index.html`. Template variables via `page.extra`: `posts` (list of `{title, link, date, date_label, topic, excerpt}`), `featured` (first post on page 1 or None), `chips` (list of `{name, link}`), `page_no`, `page_count`, `older_url`.

- [ ] **Step 1: Branch**

`git checkout -b feat/blog`

- [ ] **Step 2: Write failing tests** (append to `tests/test_site.py`, and change `PAGES`)

```python
PAGES = ["/", "/customer-service/blog/", "/customer-service/blog/page/2/", "/customer-service/blog/page/3/"]


def _posts(p):
    return [a for t, a in p.tags if t == "article" and "post" in a.get("class", "").split()]


def test_blog_page_one(site):
    p = parse(site, "/customer-service/blog/")
    assert p.texts["h1"] == ["Tips & Resources"]
    assert p.title == "Car Insurance Tips for Chicago Drivers | Insure On The Spot"
    assert len(_posts(p)) == 12
    chips = [a["href"] for t, a in p.tags if t == "a" and a.get("data-chip") is not None]
    assert len(chips) == 14 and not any("uncategorized" in h for h in chips)
    form = [a for t, a in p.tags if t == "form" and a.get("role") == "search"][0]
    assert form["action"] == "https://www.insureonthespot.com/" and form["method"] == "get"
    assert p.find("input", name="s")
    types = {b["@type"] for b in p.jsonld}
    assert {"CollectionPage", "BreadcrumbList"} <= types


def test_blog_one_link_per_card(site):
    html = (site / "customer-service" / "blog" / "index.html").read_text(encoding="utf-8")
    cards = re.findall(r'<article class="card post.*?</article>', html, flags=re.S)
    assert len(cards) == 12
    for card in cards:
        assert len(re.findall(r"<a\b", card)) == 1


def test_blog_pagination(site):
    p3 = parse(site, "/customer-service/blog/page/3/")
    assert len(_posts(p3)) == 12
    hrefs = [a.get("href") for t, a in p3.tags if t == "a"]
    assert "https://www.insureonthespot.com/customer-service/blog/page/10/" in hrefs
    p1 = parse(site, "/customer-service/blog/")
    current = [a for t, a in p1.tags if a.get("aria-current") == "page" and t == "span"]
    assert current
    assert "Page 3" in parse(site, "/customer-service/blog/page/3/").title


def test_blog_mobile_quote_after_third_post(site):
    html = (site / "customer-service" / "blog" / "index.html").read_text(encoding="utf-8")
    grid = html.split('class="post-grid"', 1)[1]
    first_quote = grid.index('class="quote-inline"')
    assert grid[:first_quote].count('<article class="card post') == 3
```

Run: `py -3.11 -m pytest tests/test_site.py -q`
Expected: FAIL (blog files missing).

- [ ] **Step 3: Add blog pages to `build/build.py`** (replace `pages()`)

```python
import html as _html
from datetime import date as _date


def _post_view(p, cats):
    d = _date.fromisoformat(p["date"])
    topic = next((cats[c]["name"] for c in p["categories"] if c in cats and cats[c]["slug"] not in HIDDEN_CATEGORIES), "")
    return {"title": _html.unescape(p["title"]), "link": p["link"], "date": p["date"],
            "date_label": f"{d:%B} {d.day}, {d.year}", "topic": _html.unescape(topic),
            "excerpt": clean_excerpt(p["excerpt_html"])}


def blog_pages(ctx):
    cats = {c["id"]: c for c in _json("categories.json")}
    chips = [{"name": _html.unescape(c["name"]), "link": c["link"]}
             for c in sorted(cats.values(), key=lambda c: c["name"]) if c["slug"] not in HIDDEN_CATEGORIES]
    posts = [_post_view(p, cats) for p in _json("posts.json")]
    out = []
    for n, chunk in enumerate(paginate(posts, PER_PAGE, BLOG_PAGES), start=1):
        rel = "customer-service/blog" + ("" if n == 1 else f"/page/{n}")
        url = f"{PROD}/{rel}/"
        title = ("Car Insurance Tips for Chicago Drivers" if n == 1 else f"Car Insurance Tips, Page {n}") + " | Insure On The Spot"
        desc = ("Car insurance tips for Chicago drivers from Insure On The Spot: claims, coverage, SR-22, "
                "safety, maintenance and getting around Chicagoland.")
        if n > 1:
            desc = f"Page {n} of our car insurance tips for Chicago drivers: claims, coverage, SR-22, safety and more."
        crumbs = [("Home", ctx["links"]["home"]), ("Tips & Resources", "/customer-service/blog/")]
        out.append(("blog.html", rel, {
            "slug": "blog", "path": "/customer-service/blog/", "title": title, "description": desc,
            "crumbs": crumbs + ([(f"Page {n}", f"/{rel}/")] if n > 1 else []),
            "jsonld": [jsonld.blog_collection(url, chunk),
                       jsonld.breadcrumbs([("Home", f"{PROD}/"), ("Tips & Resources", f"{PROD}/customer-service/blog/")])],
            "extra": {"posts": chunk[1:] if n == 1 else chunk, "featured": chunk[0] if n == 1 else None,
                      "chips": chips, "page_no": n, "page_count": BLOG_PAGES,
                      "older_url": ctx["links"]["blog_older"]},
        }))
    return out


def pages(ctx: dict) -> list[tuple[str, str, dict]]:
    home = ("index.html", "", {"slug": "home", "path": "/", "title": "Insure On The Spot preview: 3 rebuilt pages",
                               "description": "Trial task preview for Vela: rebuilt blog, locations and contact pages for Insure On The Spot, with an audit of what was fixed and why.",
                               "jsonld": [], "crumbs": []})
    return [home] + blog_pages(ctx)
```

- [ ] **Step 4: Write `templates/blog.html`**

```jinja
{% extends "base.html" %}
{% from "_macros.html" import quote_box, crumbs %}
{% macro post_card(post, featured=False) %}
<article class="card post{% if featured %} post-featured{% endif %}">
  <p class="meta">{% if post.topic %}<span class="topic">{{ post.topic }}</span>{% endif %}<time datetime="{{ post.date }}">{{ post.date_label }}</time></p>
  <h2 class="post-title"><a href="{{ post.link }}">{{ post.title }}</a></h2>
  <p>{{ post.excerpt }}</p>
  <span class="more" aria-hidden="true">Read article {{ icons['caret-right'] | safe }}</span>
</article>
{% endmacro %}
{% block main %}
<div class="page-head">
  <div class="wrap section">
    {{ crumbs(page.crumbs) }}
    <h1>Tips &amp; Resources</h1>
    <p class="lede">Practical car insurance advice for Chicago drivers: claims, coverage, SR-22s, safety and keeping your car on the road.</p>
  </div>
</div>
<div class="wrap section blog-layout">
  <div>
    <div class="blog-tools">
      <form class="search" role="search" action="{{ links.search }}" method="get">
        <label class="visually-hidden" for="blog-search">Search articles</label>
        <input id="blog-search" name="s" type="search" placeholder="Search articles, for example SR22">
        <button class="btn btn-primary" type="submit">{{ icons['magnifying-glass'] | safe }}Search</button>
      </form>
      <nav aria-label="Topics"><ul class="chips">{% for c in chips %}<li><a data-chip href="{{ c.link }}">{{ c.name }}</a></li>{% endfor %}</ul></nav>
    </div>
    <ul class="post-grid">
      {% if featured %}<li class="post-featured-item" style="grid-column:1/-1">{{ post_card(featured, True) }}</li>{% endif %}
      {% for post in posts %}
      <li>{{ post_card(post) }}</li>
      {% if loop.index == (2 if featured else 3) %}<li class="quote-inline">{{ quote_box('inline', heading='h2') }}</li>{% endif %}
      {% endfor %}
    </ul>
    <nav aria-label="Article pages">
      <ul class="pagination">
        {% for n in range(1, page_count + 1) %}
        <li>{% if n == page_no %}<span aria-current="page">{{ n }}</span>{% else %}<a href="/customer-service/blog/{% if n > 1 %}page/{{ n }}/{% endif %}">{{ n }}</a>{% endif %}</li>
        {% endfor %}
        {% if page_no < page_count %}<li><a href="/customer-service/blog/page/{{ page_no + 1 }}/">Next {{ icons['caret-right'] | safe }}</a></li>
        {% else %}<li><a href="{{ older_url }}">Older articles {{ icons['caret-right'] | safe }}</a></li>{% endif %}
      </ul>
    </nav>
  </div>
  <aside class="blog-side" aria-label="Get help">
    {{ quote_box('side', heading='h2') }}
    <section class="card" aria-labelledby="help-h">
      <h2 id="help-h">Need help?</h2>
      <ul class="help-list">
        <li><a href="{{ links.payment_options }}">{{ icons['credit-card'] | safe }}Payment options</a></li>
        <li><a href="{{ links.roadside }}">{{ icons.truck | safe }}Roadside assistance</a></li>
        <li><a href="{{ links.claim }}">{{ icons['file-text'] | safe }}Report an auto insurance claim</a></li>
        <li><a href="{{ links.faq }}">{{ icons.question | safe }}Auto insurance FAQs</a></li>
      </ul>
    </section>
  </aside>
</div>
{% endblock %}
```

The featured card counts toward the "3 posts before the inline quote box" rule (featured + 2), which the test checks.

- [ ] **Step 5: Build, test, look**

Run: `py -3.11 build/build.py && py -3.11 -m pytest -q`
Expected: all pass. Then screenshot `/customer-service/blog/` at 1440 and 393 and check: chips scroll sideways on phone, featured card full width, quote box after 3rd post on phone and in the sidebar on desktop.

Add the blog link to `templates/index.html` is already present.

- [ ] **Step 6: Commit, push, PR (stacked on foundation)**

```bash
git add build/build.py templates/blog.html tests/test_site.py site
git commit -m "Blog landing: real H1, topic chips, search, one-link cards, 3 static pages"
git push -u origin feat/blog
gh pr create --base feat/foundation --head feat/blog --title "Blog landing page" --body "Fixes FINDINGS #3, #4, #13, #14, #15, #16. 36 real posts from their REST API, 12 per page, older posts continue on the live blog at page 10."
vercel deploy
```

---

### Task 5: Locations page + lazy map

**Files:**
- Create: `templates/locations.html`, `static/js/map.js`
- Modify: `build/build.py` (`pages()`), `tests/test_site.py`

**Interfaces:**
- Consumes: `branch_card`, `quote_box`, `crumbs`, `jsonld.agency`, `jsonld.breadcrumbs`, `branches` (with `hours_rows`, `directions`), `images['locations-hero.webp']`, `links.gmaps_all`.
- Produces: `site/locations/index.html`; map DOM contract `<div class="map-panel" data-map data-points='[{"name","address","phone","tel","lat","lng"}]'><div class="map-canvas" ...></div>...`. `map.js` exports `initMap()`.

- [ ] **Step 1: Branch**

`git checkout -b feat/locations`

- [ ] **Step 2: Write failing tests** (append; add `"/locations/"` to `PAGES`)

```python
PAGES = ["/", "/customer-service/blog/", "/customer-service/blog/page/2/", "/customer-service/blog/page/3/", "/locations/"]


def test_locations_cards(site):
    p = parse(site, "/locations/")
    assert p.texts["h1"] == ["Our Locations"]
    html = p.html
    assert html.count('<article class="card branch"') == 4
    for tel in ["tel:+17732025060", "tel:+17732020651", "tel:+17088577661", "tel:+17085471800"]:
        assert f'href="{tel}"' in html
    assert html.count("Holiday hours may vary, call to confirm.") == 4
    assert html.count("data-hours=") == 4
    assert "Mon-Fri" in html and "9:30 AM to 6:00 PM" in html and "8:00 AM to 2:00 PM" in html


def test_locations_schema_and_map(site):
    p = parse(site, "/locations/")
    agencies = [b for b in p.jsonld if b["@type"] == "InsuranceAgency"]
    assert len(agencies) == 4
    assert all(b["address"]["addressRegion"] == "IL" and b["openingHoursSpecification"] for b in agencies)
    panel = [a for t, a in p.tags if "data-map" in a][0]
    points = json.loads(panel["data-points"])
    assert len(points) == 4 and all(41.6 < x["lat"] < 42.1 for x in points)
    assert "https://www.google.com/maps/search/?api=1&amp;query=Insure+On+The+Spot+Chicago+IL" in p.html


def test_locations_title(site):
    assert parse(site, "/locations/").title == "Chicago, Berwyn & Melrose Park Offices | Insure On The Spot"
```

Run: `py -3.11 -m pytest tests/test_site.py -q` → FAIL (page missing).

- [ ] **Step 3: Add the page in `build/build.py`** (inside `pages()` return, plus helper)

```python
def locations_page(ctx):
    points = [{"name": b["name"], "address": f"{b['street']}, {b['city']}, {b['state']} {b['zip']}",
               "phone": b["phone"], "tel": b["tel"], "lat": b["lat"], "lng": b["lng"]} for b in ctx["branches"]]
    return ("locations.html", "locations", {
        "slug": "locations", "path": "/locations/",
        "title": "Chicago, Berwyn & Melrose Park Offices | Insure On The Spot",
        "description": ("Visit Insure On The Spot in Chicago (N Elston Ave and S Cicero Ave), Berwyn and Melrose Park. "
                        "Hours, phone numbers, directions and free parking."),
        "crumbs": [("Home", ctx["links"]["home"]), ("Locations", "/locations/")],
        "jsonld": [jsonld.agency(b) for b in ctx["branches"]] +
                  [jsonld.breadcrumbs([("Home", f"{PROD}/"), ("Locations", f"{PROD}/locations/")])],
        "extra": {"points": points},
    })
```

and change the `pages()` return to `return [home] + blog_pages(ctx) + [locations_page(ctx)]`.

- [ ] **Step 4: Write `templates/locations.html`**

```jinja
{% extends "base.html" %}
{% from "_macros.html" import branch_card, quote_box, crumbs %}
{% block main %}
<div class="page-head">
  <div class="wrap page-head-grid">
    <div class="page-head-text">
      {{ crumbs(page.crumbs) }}
      <h1>Our Locations</h1>
      <p class="lede">Come in and see us! Our friendly staff is here to help. Get a free quote, buy, renew your policy, or make a payment at any of our Chicagoland offices.</p>
      <ul class="facts">
        <li>{{ icons.storefront | safe }}4 offices</li>
        <li>{{ icons.car | safe }}Free parking at each</li>
      </ul>
    </div>
    <div class="page-head-photo">
      <img src="/assets/img/locations-hero.webp" alt="Smiling Insure On The Spot agent leaning out of a car window" width="{{ images['locations-hero.webp'][0] }}" height="{{ images['locations-hero.webp'][1] }}" fetchpriority="high">
    </div>
  </div>
</div>
<section class="wrap section" aria-labelledby="offices-h">
  <h2 id="offices-h" class="section-title">Find an office near you</h2>
  <div class="loc-layout">
    <ul class="branch-list">
      {% for b in branches %}<li>{{ branch_card(b, heading='h3') }}</li>{% endfor %}
    </ul>
    <div class="map-panel" data-map data-points='{{ points | tojson }}'>
      <div class="map-canvas" role="region" aria-label="Map of our 4 offices"></div>
      <p class="link-row"><a href="{{ links.gmaps_all }}" target="_blank" rel="noopener">{{ icons['map-pin'] | safe }}View on Google Maps</a><a href="{{ links.location_finder }}">Location Finder</a><a href="{{ links.service_areas }}">Additional areas served</a></p>
    </div>
  </div>
</section>
<section class="wrap section after-grid" aria-label="Offers">
  <div class="promo">
    <h2>{{ icons.gift | safe }} Free $100 Amazon gift card</h2>
    <p>Refer friends and family. They mention your client code, and when their policy starts you get a $100 gift card.</p>
  </div>
  {{ quote_box('locations', heading='h2') }}
</section>
{% endblock %}
```

- [ ] **Step 5: Write `static/js/map.js`**

```js
function loadCss(href) {
  return new Promise((resolve, reject) => {
    const link = Object.assign(document.createElement('link'), { rel: 'stylesheet', href });
    link.onload = resolve; link.onerror = reject;
    document.head.append(link);
  });
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = Object.assign(document.createElement('script'), { src, async: true });
    s.onload = resolve; s.onerror = reject;
    document.head.append(s);
  });
}

function popup(p) {
  const el = document.createElement('div');
  const name = document.createElement('strong');
  name.textContent = p.name;
  const addr = document.createElement('div');
  addr.textContent = p.address;
  const tel = Object.assign(document.createElement('a'), { href: `tel:${p.tel}`, textContent: p.phone });
  el.append(name, addr, tel);
  return el;
}

export function initMap() {
  const panel = document.querySelector('[data-map]');
  if (!panel || !('IntersectionObserver' in window)) return;
  const canvas = panel.querySelector('.map-canvas');
  const load = async () => {
    try {
      await loadCss('/assets/vendor/leaflet/leaflet.css');
      await loadScript('/assets/vendor/leaflet/leaflet.js');
      const L = window.L;
      const points = JSON.parse(panel.dataset.points);
      const map = L.map(canvas, { scrollWheelZoom: false });
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);
      points.forEach((p) => L.marker([p.lat, p.lng], { title: p.name, alt: p.name }).addTo(map).bindPopup(popup(p)));
      map.fitBounds(points.map((p) => [p.lat, p.lng]), { padding: [36, 36] });
      panel.classList.add('is-loaded');
    } catch (error) {
      panel.classList.add('is-failed');
      canvas.hidden = true;
    }
  };
  const io = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) { io.disconnect(); load(); }
  }, { rootMargin: '300px' });
  io.observe(panel);
}
```

- [ ] **Step 6: Build, test, look**

Run: `py -3.11 build/build.py && py -3.11 -m pytest -q && npm run test:js`
Expected: all pass. Screenshot `/locations/` at 1440 and 393 (scroll to the map first so it loads); compare with the approved mockup `direction-b-v2b.html` / `iphone-mobile-v2.html`.

- [ ] **Step 7: Commit, push, PR**

```bash
git add build/build.py templates/locations.html static/js/map.js tests/test_site.py site
git commit -m "Locations: tap-to-call, hours on every card, live status, map, branch schema"
git push -u origin feat/locations
gh pr create --base feat/blog --head feat/locations --title "Locations page" --body "Fixes FINDINGS #1, #2, #5, #9, #10, #11, #12, #20, #25 (badge in footer)."
vercel deploy
```

---

### Task 6: Contact page

**Files:**
- Create: `templates/contact.html`
- Modify: `build/build.py` (`pages()`), `tests/test_site.py`

**Interfaces:**
- Consumes: `branch_card(compact=True)`, `status`, `hours_list`, `quote_box`, `crumbs`, `departments`, `jsonld.contact_page`, `jsonld.breadcrumbs`, `jsonld.organization`, `images['contact-photo.webp']`.
- Produces: `site/contact/index.html`.

- [ ] **Step 1: Branch**

`git checkout -b feat/contact`

- [ ] **Step 2: Write failing tests** (append; add `"/contact/"` to `PAGES`)

```python
PAGES = ["/", "/customer-service/blog/", "/customer-service/blog/page/2/", "/customer-service/blog/page/3/", "/locations/", "/contact/"]


def test_contact_page(site):
    p = parse(site, "/contact/")
    assert p.texts["h1"] == ["Contact Us"]
    assert p.title == "Contact Insure On The Spot | Call 773-202-5060"
    html = p.html
    assert 'class="big-phone" href="tel:+17732025060"' in html
    assert html.count('class="card dept"') == 2
    assert "8:00 AM to 8:30 PM" in html and "8:00 AM to 5:00 PM" in html
    assert html.count("Holiday hours may vary, call to confirm.") == 2
    assert html.count('<article class="card branch"') == 4
    forms = [a for t, a in p.tags if t == "form"]
    assert forms and all("data-quote" in a for a in forms), "no contact form, only quote forms"
    assert "/assets/img/contact-photo.webp" in html and "iots-hero" not in html
    assert "Chicago&#39;s #1 Auto Insurance Agency" in html or "Chicago's #1 Auto Insurance Agency" in html
    types = {b["@type"] for b in p.jsonld}
    assert {"ContactPage", "BreadcrumbList"} <= types


def test_contact_task_links(site):
    p = parse(site, "/contact/")
    hrefs = {a.get("href") for t, a in p.tags if t == "a"}
    for url in ["https://quote.insureonthespot.com/", "https://csp.insureonthespot.com/Login.aspx",
                "https://www.insureonthespot.com/customer-service/report-insurance-claim/",
                "https://www.insureonthespot.com/customer-service/roadside-assistance/",
                "https://www.insureonthespot.com/customer-service/auto-insurance-faq/",
                "https://www.insureonthespot.com/see-what-our-customers-are-saying-about-us/",
                "https://www.insureonthespot.com/employment-opportunities/"]:
        assert url in hrefs, url
```

Run → FAIL.

- [ ] **Step 3: Add the page in `build/build.py`**

```python
def contact_page(ctx):
    return ("contact.html", "contact", {
        "slug": "contact", "path": "/contact/",
        "title": "Contact Insure On The Spot | Call 773-202-5060",
        "description": ("Call Insure On The Spot at 773-202-5060 or visit one of 4 Chicagoland offices. "
                        "Customer service and sales hours, payments, claims and free quotes."),
        "crumbs": [("Home", ctx["links"]["home"]), ("Contact Us", "/contact/")],
        "jsonld": [jsonld.contact_page(),
                   jsonld.breadcrumbs([("Home", f"{PROD}/"), ("Contact Us", f"{PROD}/contact/")])],
    })
```

`pages()` returns `[home] + blog_pages(ctx) + [locations_page(ctx), contact_page(ctx)]`.

- [ ] **Step 4: Write `templates/contact.html`**

```jinja
{% extends "base.html" %}
{% from "_macros.html" import branch_card, quote_box, crumbs, status, hours_list %}
{% block main %}
<div class="page-head">
  <div class="wrap page-head-grid">
    <div class="page-head-text">
      {{ crumbs(page.crumbs) }}
      <p class="eyebrow">Chicago's #1 Auto Insurance Agency</p>
      <h1>Contact Us</h1>
      <p class="lede">Call us, stop by one of our 4 Chicagoland offices, or handle it online.</p>
      <a class="big-phone" href="tel:{{ main_tel }}">{{ icons.phone | safe }}{{ main_phone }}</a>
    </div>
    <div class="page-head-photo">
      <img src="/assets/img/contact-photo.webp" alt="Insure On The Spot agent in a branded shirt holding a toy car" width="{{ images['contact-photo.webp'][0] }}" height="{{ images['contact-photo.webp'][1] }}" fetchpriority="high" style="object-position:50% 25%">
    </div>
  </div>
</div>
<div class="wrap section contact-grid">
  <div>
    <section aria-labelledby="hours-h">
      <h2 id="hours-h">Phone hours</h2>
      <div class="dept-grid">
        {% for d in departments %}
        <article class="card dept">
          <div class="branch-head"><h3>{{ d.name }}</h3>{{ status(d.hours) }}</div>
          {{ hours_list(d.hours_rows) }}
          <p class="holiday">{{ holiday_note }}</p>
        </article>
        {% endfor %}
      </div>
    </section>
    <section class="section" aria-labelledby="tasks-h">
      <h2 id="tasks-h">What do you need?</h2>
      <ul class="tasks">
        <li><a href="{{ links.quote }}">{{ icons.car | safe }}Get a free quote</a></li>
        <li><a href="{{ links.portal }}">{{ icons['credit-card'] | safe }}Make a payment</a></li>
        <li><a href="{{ links.portal }}">{{ icons['arrows-clockwise'] | safe }}Renew my policy</a></li>
        <li><a href="{{ links.claim }}">{{ icons['file-text'] | safe }}Report a claim</a></li>
        <li><a href="{{ links.roadside }}">{{ icons.truck | safe }}Roadside assistance</a></li>
        <li><a href="{{ links.faq }}">{{ icons.question | safe }}Auto insurance FAQs</a></li>
      </ul>
    </section>
    <section aria-labelledby="visit-h">
      <h2 id="visit-h">Visit a branch</h2>
      <ul class="branch-mini">
        {% for b in branches %}<li>{{ branch_card(b, heading='h3', compact=True) }}</li>{% endfor %}
      </ul>
      <p class="link-row"><a href="/locations/">See all hours and the map {{ icons['caret-right'] | safe }}</a></p>
    </section>
  </div>
  <aside class="contact-side" aria-label="More ways we can help">
    {{ quote_box('contact', heading='h2') }}
    <div class="promo">
      <h2>{{ icons.gift | safe }} Free $100 Amazon gift card</h2>
      <p>Refer friends and family. They mention your client code, and when their policy starts you get a $100 gift card.</p>
    </div>
    <div class="card trust">
      <a href="{{ links.reviews }}">{{ icons.star | safe }} See what our customers are saying</a>
      <a href="{{ links.bbb }}"><img src="/assets/img/bbb.png" alt="BBB Accredited Business, view Insure On The Spot on BBB" width="{{ images['bbb.png'][0] }}" height="{{ images['bbb.png'][1] }}" loading="lazy"></a>
    </div>
    <div class="card">
      <h2>{{ icons.briefcase | safe }} Work with us</h2>
      <p>Interested in working with a constantly growing and exciting organization in the Chicago-land area?</p>
      <a href="{{ links.employment }}">See employment opportunities</a>
    </div>
  </aside>
</div>
{% endblock %}
```

- [ ] **Step 5: Build, test, look**

Run: `py -3.11 build/build.py && py -3.11 -m pytest -q`
Expected: all pass. Screenshot `/contact/` at 1440 and 393.

- [ ] **Step 6: Commit, push, PR**

```bash
git add build/build.py templates/contact.html tests/test_site.py site
git commit -m "Contact: real hero text, phone hours with status, task shortcuts, branch list"
git push -u origin feat/contact
gh pr create --base feat/locations --head feat/contact --title "Contact page" --body "Fixes FINDINGS #5, #6, #7, #8 (quote box), #10, #12. No contact form on purpose: needs their decision on who answers and where leads go."
vercel deploy
```

---

### Task 7: QA in real browsers (accessibility, layout, failure modes, links, performance)

**Files:**
- Create: `qa/serve.py`, `qa/check_browser.py`, `qa/check_links.py`, `qa/lighthouse.sh`
- Modify: any template/CSS file where QA finds a problem

**Interfaces:**
- Consumes: built `site/`; `node_modules/axe-core/axe.min.js`.
- Produces: `qa/out/browser.json`, `qa/out/links.json`, `qa/out/lh-*.json`, `qa/out/summary.md` (numbers used in the note).

- [ ] **Step 1: Branch**

`git checkout -b chore/qa`

- [ ] **Step 2: Write `qa/serve.py`** (a server the tests start and stop themselves)

```python
import contextlib
import functools
import http.server
import threading
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"


@contextlib.contextmanager
def serve(port=8765):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
```

- [ ] **Step 3: Write `qa/check_browser.py`** (pytest file, runs against the local build)

```python
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from serve import serve

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "qa" / "out"
PAGES = ["/customer-service/blog/", "/locations/", "/contact/"]
AXE = (ROOT / "node_modules" / "axe-core" / "axe.min.js").read_text(encoding="utf-8")
RESULTS = {}


@pytest.fixture(scope="module")
def base():
    with serve() as url:
        yield url


@pytest.fixture(scope="module")
def pw():
    with sync_playwright() as p:
        yield p


@pytest.mark.parametrize("engine", ["chromium", "firefox", "webkit"])
@pytest.mark.parametrize("width", [320, 390, 768, 1440])
def test_no_horizontal_overflow_and_no_errors(pw, base, engine, width):
    browser = getattr(pw, engine).launch()
    ctx = browser.new_context(viewport={"width": width, "height": 900})
    for path in PAGES:
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base + path, wait_until="load")
        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        assert overflow <= 0, f"{engine} {width} {path} overflows by {overflow}px"
        assert not errors, f"{engine} {width} {path}: {errors}"
        page.close()
    browser.close()


@pytest.mark.parametrize("width", [390, 1440])
def test_axe_no_serious_violations(pw, base, width):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": 900})
    for path in PAGES:
        page.goto(base + path, wait_until="load")
        page.add_script_tag(content=AXE)
        res = page.evaluate("axe.run(document, {resultTypes: ['violations']})")
        bad = [v for v in res["violations"] if v["impact"] in ("serious", "critical")]
        RESULTS.setdefault("axe", {})[f"{path}@{width}"] = [v["id"] for v in res["violations"]]
        assert not bad, f"{path}@{width}: {[(v['id'], len(v['nodes'])) for v in bad]}"
    browser.close()


def test_status_uses_chicago_time(pw, base):
    browser = pw.chromium.launch()
    ctx = browser.new_context(timezone_id="Asia/Manila")
    page = ctx.new_page()
    page.clock.set_fixed_time(datetime(2026, 10, 6, 23, 30, tzinfo=timezone.utc))  # Tue 6:30 PM in Chicago
    page.goto(base + "/locations/", wait_until="load")
    labels = page.locator(".branch .status").all_inner_texts()
    assert labels[0] == "Open, closes 8 PM"
    assert labels[1] == "Closed, opens tomorrow 9:30 AM"
    assert page.locator('.branch').first.locator('[data-day~="tue"]').evaluate("el => el.classList.contains('is-today')")
    browser.close()


def test_no_js_page_still_works(pw, base):
    browser = pw.chromium.launch()
    ctx = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 900})
    page = ctx.new_page()
    page.goto(base + "/locations/")
    assert page.locator(".hours").first.is_visible()
    assert page.locator('a[href="tel:+17732020651"]').count() == 1
    assert page.locator("#site-menu a").first.is_visible()  # menu shown without JS
    form = page.locator("form[data-quote]").first
    assert form.get_attribute("action") == "https://quote.insureonthespot.com/" and form.get_attribute("method") == "get"
    browser.close()


def test_quote_validation_in_browser(pw, base):
    browser = pw.chromium.launch()
    page = browser.new_page()
    seen = []
    page.route("https://quote.insureonthespot.com/**", lambda route: (seen.append(route.request.url), route.abort()))
    page.goto(base + "/contact/", wait_until="load")
    box = page.locator("#zip-contact")
    box.fill("6063")
    page.locator("form:has(#zip-contact) button").click()
    assert page.locator("#zip-err-contact").inner_text() == "Enter a 5-digit ZIP code, like 60630."
    assert box.get_attribute("aria-invalid") == "true"
    box.fill("60630")
    page.locator("form:has(#zip-contact) button").click()
    page.wait_for_timeout(500)
    assert seen and seen[-1] == "https://quote.insureonthespot.com/?zipcode=60630"
    browser.close()


def test_menu_keyboard(pw, base):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 390, "height": 900})
    page.goto(base + "/contact/", wait_until="load")
    toggle = page.locator("[data-menu-toggle]")
    assert page.locator("#site-menu").is_hidden()
    toggle.focus(); page.keyboard.press("Enter")
    assert toggle.get_attribute("aria-expanded") == "true" and page.locator("#site-menu").is_visible()
    page.keyboard.press("Escape")
    assert toggle.get_attribute("aria-expanded") == "false"
    assert page.evaluate("document.activeElement.hasAttribute('data-menu-toggle')")
    browser.close()


def test_map_failure_is_graceful(pw, base):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route("**/vendor/leaflet/**", lambda r: r.abort())
    page.route("https://tile.openstreetmap.org/**", lambda r: r.abort())
    page.goto(base + "/locations/", wait_until="load")
    page.locator(".map-panel").scroll_into_view_if_needed()
    page.wait_for_timeout(1500)
    assert page.locator(".map-panel").evaluate("el => el.classList.contains('is-failed')")
    assert page.get_by_role("link", name="View on Google Maps").is_visible()
    assert not errors
    browser.close()


def test_map_loads_four_pins(pw, base):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(base + "/locations/", wait_until="load")
    page.locator(".map-panel").scroll_into_view_if_needed()
    page.wait_for_selector(".leaflet-marker-icon", timeout=15000)
    assert page.locator(".leaflet-marker-icon").count() == 4
    browser.close()


def teardown_module():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "browser.json").write_text(json.dumps(RESULTS, indent=1), encoding="utf-8")
```

Run:
```bash
py -3.11 -m playwright install firefox webkit
py -3.11 -m pytest qa/check_browser.py -q -p no:cacheprovider --rootdir qa
```
Expected: all pass. For each failure, fix the template/CSS, rebuild (`py -3.11 build/build.py`), rerun the one failing test, then the whole file.

- [ ] **Step 4: Write `qa/check_links.py`**

```python
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
```

Run: `py -3.11 qa/check_links.py`
Expected: `checked=N failures=[]`. A 403 from bbb.org to scripts is acceptable only after opening that URL in a real browser and confirming it loads; record it in `qa/out/summary.md` if so.

- [ ] **Step 5: Write `qa/lighthouse.sh`** (mobile, ours vs live)

```bash
#!/usr/bin/env bash
# Usage: bash qa/lighthouse.sh https://<our-deployment>
set -euo pipefail
OURS="$1"
CHROME_PATH="$(py -3.11 -c 'from playwright.sync_api import sync_playwright as s; p=s().start(); print(p.chromium.executable_path); p.stop()')"
export CHROME_PATH
mkdir -p qa/out
for path in customer-service/blog locations contact; do
  name="${path##*/}"
  for side in ours live; do
    base="$OURS"; [ "$side" = live ] && base="https://www.insureonthespot.com"
    npx --yes lighthouse "$base/$path/" --quiet --form-factor=mobile \
      --only-categories=performance,accessibility,best-practices \
      --chrome-flags="--headless=new" --output=json --output-path="qa/out/lh-$side-$name.json" || true
  done
done
py -3.11 - <<'EOF'
import json, glob
rows = []
for f in sorted(glob.glob("qa/out/lh-*.json")):
    d = json.load(open(f, encoding="utf-8"))
    c = d["categories"]
    rows.append(f"| {f.split('lh-')[1][:-5]} | {round(c['performance']['score']*100)} | {round(c['accessibility']['score']*100)} | {round(c['best-practices']['score']*100)} | {d['audits']['largest-contentful-paint']['displayValue']} |")
open("qa/out/summary.md", "w", encoding="utf-8").write("| page | perf | a11y | best practices | LCP |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
print(open("qa/out/summary.md", encoding="utf-8").read())
EOF
```

SEO category is skipped on purpose: our pages are noindexed, so Lighthouse SEO would flag them by design.

Run (after `vercel deploy`): `bash qa/lighthouse.sh <preview-url>`
Expected: a table in `qa/out/summary.md`. If the preview URL needs a Vercel login, run against `py -3.11 -m http.server` locally instead and note "local" in the summary.

- [ ] **Step 6: Commit, PR**

```bash
git add qa site templates static build
git commit -m "QA: cross-browser layout, axe, failure modes, link check, Lighthouse"
git push -u origin chore/qa
gh pr create --base feat/contact --head chore/qa --title "QA scripts and fixes" --body "Playwright (Chromium, Firefox, WebKit at 320/390/768/1440), axe, no-JS, Chicago-time status from Manila, map failure, link check, Lighthouse vs live."
```

---

### Task 8: Deliverables, production deploy, submit checklist

**Files:**
- Create: `qa/shoot.py`, `deliverables/screenshots/*.png`, `deliverables/NOTE.md`

**Interfaces:**
- Consumes: deployed production URL, `qa/out/summary.md`, `docs/FINDINGS.md`.
- Produces: 6 screenshots, the note draft, the submitted URL.

- [ ] **Step 1: Write `qa/shoot.py`**

```python
"""Full-page screenshots for the submission: desktop 1440 and iPhone 15 Pro 393x852."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deliverables" / "screenshots"
PAGES = {"blog": "/customer-service/blog/", "locations": "/locations/", "contact": "/contact/"}
VIEWS = {
    "desktop": dict(viewport={"width": 1440, "height": 900}, device_scale_factor=1),
    "mobile": dict(viewport={"width": 393, "height": 852}, device_scale_factor=3, is_mobile=True, has_touch=True,
                   user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"),
}


def main(base):
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for view, opts in VIEWS.items():
            ctx = browser.new_context(**opts)
            for name, path in PAGES.items():
                page = ctx.new_page()
                page.goto(base + path, wait_until="load")
                if name == "locations":
                    page.locator(".map-panel").scroll_into_view_if_needed()
                    page.wait_for_selector(".leaflet-marker-icon", timeout=15000)
                    page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(800)
                page.screenshot(path=OUT / f"{name}-{view}.png", full_page=True)
                page.close()
            ctx.close()
        browser.close()
    print(sorted(f.name for f in OUT.glob("*.png")))


if __name__ == "__main__":
    main(sys.argv[1].rstrip("/"))
```

- [ ] **Step 2: Wrenz reviews and merges the stacked PRs in order** (foundation, blog, locations, contact, qa) on GitHub after his shift. Then:

```bash
git checkout main && git pull
py -3.11 build/build.py && py -3.11 -m pytest -q && npm run test:js
vercel deploy --prod
```
Record the production URL (`https://iots-trial*.vercel.app`).

- [ ] **Step 3: Production checks (logged out, headers, trailing slash)**

```bash
URL=https://<production-domain>
curl -s -o /dev/null -w "%{http_code}\n" "$URL/locations/"            # expect 200 (not 401)
curl -sI "$URL/locations/" | grep -i x-robots-tag                     # expect noindex, nofollow
curl -s "$URL/robots.txt"                                             # expect Allow: /
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" "$URL/locations"   # expect 308 -> /locations/
```
Then open `$URL/` in a private browser window (logged out of Vercel) and click through all three pages. Wrenz opens it on his phone too.

- [ ] **Step 4: Screenshots**

Run: `py -3.11 qa/shoot.py https://<production-domain>`
Expected: `['blog-desktop.png', 'blog-mobile.png', 'contact-desktop.png', 'contact-mobile.png', 'locations-desktop.png', 'locations-mobile.png']`. Open each and check nothing is cut off or overlapping.

- [ ] **Step 5: Write `deliverables/NOTE.md`** (Wrenz rewrites in his voice; numbers come from `qa/out/summary.md`)

```markdown
Preview: <production URL> (noindexed on purpose; robots.txt left open so Google can see the noindex)

What I tested
- Chrome, Firefox and Safari's engine at 320, 390, 768 and 1440px: no sideways scrolling, no script errors. Also on my own phone.
- Accessibility: axe scan with no serious or critical issues, plus a keyboard-only pass (menu, topic chips, buttons, map).
- Every link and phone number on the three pages, the ZIP quote box (valid and invalid ZIPs), the pages with JavaScript off, and the open/closed labels from a different time zone.
- Lighthouse mobile, ours vs live: <copy the 3 perf numbers from qa/out/summary.md>. Part of the gap is that the preview has none of your marketing tags.

Improvements and why
1. Locations: every branch is tap-to-call, hours are on the card with a live open/closed label in Chicago time. Before, branch numbers weren't tappable and hours were behind four extra pages.
2. SEO basics: meta descriptions (there were none), a real H1 on the blog, correct heading order, alt text, and local business schema for each branch.
3. Contact: removed the hero overlap and the blank gaps, added the branches and quick links for payments, claims and roadside.

Also found: the Español link goes to one Spanish page with no way back to English, marked as English, with no hreflang. And a question: should the contact page have a form? If so, who answers it and where should leads go?

Tools: Claude Code, Python (data pulled from your WordPress REST API), Playwright, axe, Lighthouse, GitHub, Vercel.
```

- [ ] **Step 6: Commit and final PR**

```bash
git checkout -b chore/deliverables
git add qa/shoot.py deliverables
git commit -m "Add submission screenshots and note draft"
git push -u origin chore/deliverables
gh pr create --base main --head chore/deliverables --title "Submission deliverables" --body "Screenshots (desktop + iPhone 15 Pro) and the note draft."
```

- [ ] **Step 7: Submit** (Wrenz): open the personal task link from the "Trial task from Vela" email, paste the production URL, attach the 6 screenshots, paste the rewritten note. Before sending: the URL opens logged out, and the note is in his own words.
