import json
import re
from pathlib import Path

import pytest

from conftest import ROOT, parse

PAGES = ["/", "/customer-service/blog/", "/customer-service/blog/page/2/", "/customer-service/blog/page/3/", "/locations/", "/contact/"]


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
    chips = [a["href"] for t, a in p.tags if t == "a" and a.get("data-topic")]
    assert len(chips) == 14 and not any("uncategorized" in h for h in chips)
    assert all(h.startswith("https://www.insureonthespot.com/category/") for h in chips)
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
    pager = p1.html.split('class="pagination"', 1)[1].split("</nav>", 1)[0]
    assert 'aria-current="page"' in pager
    assert "Page 3" in parse(site, "/customer-service/blog/page/3/").title


def test_blog_cta_band_after_six_cards(site):
    for rel in ["customer-service/blog", "customer-service/blog/page/2"]:
        html = (site / rel / "index.html").read_text(encoding="utf-8")
        latest = html.split('id="latest"', 1)[1]
        assert latest.split('class="cta-band"', 1)[0].count('<article class="card post') == 6, rel


def test_blog_hero_cards_and_reading_time(site):
    html = (site / "customer-service" / "blog" / "index.html").read_text(encoding="utf-8")
    assert '<section class="hero' in html and 'class="search"' in html
    cards = re.findall(r'<article class="card post.*?</article>', html, flags=re.S)
    assert len(cards) == 12
    for card in cards:
        assert 'class="cover tone-' in card and '<use href="#t-' in card
        assert re.search(r"\d+ min read", card)
    assert 'class="ask-tile"' in html  # fills the 12th grid cell on page 1


def test_search_index_file(site):
    import gzip
    raw = (site / "assets" / "data" / "posts-index.json").read_bytes()
    data = json.loads(raw)
    assert data["count"] == len(data["posts"]) >= 590
    assert len(gzip.compress(raw)) < 60_000
    es = [p for p in data["posts"] if p[6] == "es"]
    assert len(es) >= 40 and all(len(p) == 7 for p in data["posts"])



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
    agencies = [b for b in p.jsonld if "parentOrganization" in b]
    assert len(agencies) == 4
    assert all(b["address"]["addressRegion"] == "IL" and b["openingHoursSpecification"] for b in agencies)
    panel = [a for t, a in p.tags if "data-map" in a][0]
    points = json.loads(panel["data-points"])
    assert len(points) == 4 and all(41.6 < x["lat"] < 42.1 for x in points)
    assert "https://www.google.com/maps/search/?api=1&amp;query=Insure+On+The+Spot+Chicago+IL" in p.html


def test_locations_title(site):
    assert parse(site, "/locations/").title == "Chicago, Berwyn & Melrose Park Offices | Insure On The Spot"


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


def _nodes(block):
    yield block
    for v in block.values():
        if isinstance(v, dict):
            yield from _nodes(v)


@pytest.mark.parametrize("rel", ["/locations/", "/contact/"])
def test_jsonld_local_business_nodes_have_address(site, rel):
    p = parse(site, rel)
    for block in p.jsonld:
        for node in _nodes(block):
            if node.get("@type") == "InsuranceAgency":
                assert "address" in node, f"{rel}: InsuranceAgency without address: {node.get('@id')}"
            if node.get("@id", "").endswith("/#organization"):
                assert node.get("@type") in (None, "Organization"), node


@pytest.mark.parametrize("rel,title", [("/customer-service/blog/page/2/", "Seguro de Auto con Pago Inicial Bajo"),
                                       ("/customer-service/blog/page/3/", "Te Detienen Sin Seguro")])
def test_spanish_posts_are_marked_spanish(site, rel, title):
    html = (site / rel.strip("/") / "index.html").read_text(encoding="utf-8")
    card = re.search(r'<article class="card post[^>]*>(?:(?!</article>).)*' + re.escape(title), html, flags=re.S)
    assert card and re.search(r'class="post-title" lang="es"', card.group(0)), f"{title} title is not lang=es"


def test_css_has_no_font_shorthand_with_inherit():
    # `font: 700 15px inherit` is invalid CSS and silently drops the whole declaration (bit us twice)
    css = (ROOT / "static" / "css" / "site.css").read_text(encoding="utf-8")
    bad = [m for m in re.findall(r"font:[^;}]*", css) if "inherit" in m and m.replace(" ", "") != "font:inherit"]
    assert not bad, bad
