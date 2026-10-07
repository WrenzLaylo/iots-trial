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
    for name in ["logo.png", "locations-hero.webp", "contact-photo.webp", "bbb.png"]:
        assert (ROOT / "static" / "img" / name).stat().st_size < 80_000, f"{name} over 80 KB budget"
    assert (ROOT / "static" / "fonts" / "figtree-latin.woff2").stat().st_size > 10_000
    for icon in ["phone", "navigation-arrow", "clock", "storefront", "car", "list", "x",
                 "magnifying-glass", "credit-card", "arrows-clockwise", "file-text", "truck",
                 "question", "star", "briefcase", "gift", "map-pin", "caret-right"]:
        assert (ROOT / "static" / "icons" / f"{icon}.svg").exists(), icon
    for f in ["leaflet.js", "leaflet.css", "images/marker-icon.png", "images/marker-icon-2x.png", "images/marker-shadow.png"]:
        assert (ROOT / "static" / "vendor" / "leaflet" / f).exists(), f
