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
