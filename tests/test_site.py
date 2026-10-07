import json
import re
from pathlib import Path

import pytest

from conftest import ROOT, parse

PAGES = ["/", "/customer-service/blog/", "/customer-service/blog/page/2/", "/customer-service/blog/page/3/"]


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


def _posts(p):
    return [a for t, a in p.tags if t == "article" and "post" in a.get("class", "").split()]


def test_blog_page_one(site):
    p = parse(site, "/customer-service/blog/")
    assert p.texts["h1"] == ["Tips & Resources"]
    assert p.title == "Car Insurance Tips for Chicago Drivers | Insure On The Spot"
    assert len(_posts(p)) == 12
    chips = [a["href"] for t, a in p.tags if t == "a" and "data-chip" in a]
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
        assert len(re.findall(r"<a[\s>]", card)) == 1


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
