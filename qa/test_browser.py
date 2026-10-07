import json
import time
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
        bad = res["violations"]  # any impact level
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


@pytest.mark.parametrize("path", PAGES)
def test_no_js_page_still_works(pw, base, path):
    browser = pw.chromium.launch()
    ctx = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 900})
    page = ctx.new_page()
    page.goto(base + path)
    if path != "/customer-service/blog/":
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


@pytest.mark.parametrize("path", PAGES)
def test_no_layout_shift_on_phone(pw, base, path):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page.add_init_script("""
      window.__cls = 0;
      new PerformanceObserver((list) => { for (const e of list.getEntries()) { if (!e.hadRecentInput) window.__cls += e.value; } })
        .observe({ type: 'layout-shift', buffered: true });
    """)
    def slow_script(route):  # like a slow phone network: first paint happens before the module runs
        time.sleep(1.0)
        route.continue_()
    page.route("**/assets/js/site.js*", slow_script)
    page.goto(base + path, wait_until="load")
    page.wait_for_timeout(1500)
    cls = page.evaluate("window.__cls")
    RESULTS.setdefault("cls", {})[path] = round(cls, 3)
    assert cls < 0.1, f"{path}: CLS {cls:.3f}"
    browser.close()


@pytest.mark.parametrize("path", PAGES)
def test_keyboard_walk(pw, base, path):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(base + path, wait_until="load")
    if path == "/locations/":
        page.locator(".map-panel").scroll_into_view_if_needed()
        page.wait_for_selector(".leaflet-marker-icon", timeout=15000)
        page.evaluate("scrollTo(0, 0)")
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.classList.contains('skip-link')")
    reached_footer, no_ring = False, []
    for _ in range(250):
        page.keyboard.press("Tab")
        info = page.evaluate("""() => { const el = document.activeElement; const has = (n) => { const cs = getComputedStyle(n); return cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0; };
            const card = el.closest('.post');  // blog cards draw the ring on the whole card via :focus-within
            const box = el.closest('.search');  // the search field draws a 3px yellow ring on its wrapper
            const boxRing = !!box && getComputedStyle(box).boxShadow.includes('0px 0px 0px 3px');
            return { footer: !!el.closest('.site-footer'), ring: has(el) || (!!card && has(card)) || boxRing,
                     label: (el.getAttribute('aria-label') || el.textContent || el.tagName).trim().slice(0, 40) }; }""")
        if not info["ring"]:
            no_ring.append(info["label"])
        if info["footer"]:
            reached_footer = True
            break
    assert reached_footer, f"{path}: focus never reached the footer (trap?)"
    assert not no_ring, f"{path}: no visible focus ring on {no_ring[:5]}"
    browser.close()


@pytest.mark.parametrize("blocked", ["**/assets/js/site.js*", "**/assets/js/hours.js*"])
def test_menu_usable_when_script_fails(pw, base, blocked):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 390, "height": 900})
    page.route(blocked, lambda r: r.abort())
    page.goto(base + "/contact/", wait_until="load")
    page.wait_for_timeout(500)
    menu_link = page.locator("#site-menu a").first
    if not menu_link.is_visible():
        page.locator("[data-menu-toggle]").click()
    assert menu_link.is_visible(), f"menu unreachable when {blocked} fails"
    browser.close()


def test_map_does_not_trap_scrolling_on_phones(pw, base):
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 393, "height": 852}, is_mobile=True, has_touch=True,
                              user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
    page = ctx.new_page()
    page.goto(base + "/locations/", wait_until="load")
    page.locator(".map-panel").scroll_into_view_if_needed()
    page.wait_for_selector(".leaflet-marker-icon", timeout=15000)
    classes = page.locator(".map-canvas").get_attribute("class")
    assert "leaflet-touch-drag" not in classes, classes
    browser.close()


# ---------- v2 instant search ----------
BLOG = "/customer-service/blog/"


def _blog(pw, base, path=BLOG, width=1440):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base + path, wait_until="load")
    page.wait_for_selector("[data-blog-search][data-ready]", state="attached")
    return browser, page, errors


def test_instant_search_results(pw, base):
    browser, page, errors = _blog(pw, base)
    page.locator("#blog-q").press_sequentially("sr22", delay=40)
    page.wait_for_function("(document.getElementById('results-h') || {}).textContent?.includes('sr22')")
    assert "sr22" in page.inner_text("#results-h") and "guides" in page.inner_text("#results-h")
    cards = page.locator("#search-results article.post")
    assert 1 <= cards.count() <= 12
    assert "SR-22" in " ".join(page.locator("#search-results .post-title mark").all_inner_texts())
    assert "q=sr22" in page.url and page.locator("#default-view").is_hidden()
    assert not errors
    browser.close()


def test_accent_insensitive_search(pw, base):
    browser, page, _ = _blog(pw, base)
    page.fill("#blog-q", "que pasa si te detienen")
    page.wait_for_selector("#search-results article.post")
    assert page.locator("#search-results .post-title").first.inner_text().startswith("Qué")
    browser.close()


def test_empty_state_is_designed(pw, base):
    browser, page, _ = _blog(pw, base)
    page.fill("#blog-q", "zzqxv")
    page.wait_for_selector(".empty")
    assert page.inner_text("#results-h").startswith("No guides match")
    body = page.inner_text("#search-results")
    assert "0 guides" not in body and "0 results" not in body
    assert page.locator('.empty a[href="https://www.insureonthespot.com/?s=zzqxv"]').count() == 1
    assert page.locator('.empty a[href^="tel:"]').count() == 1
    assert page.locator(".empty .pop button").count() >= 4
    browser.close()


def test_did_you_mean(pw, base):
    browser, page, _ = _blog(pw, base)
    page.fill("#blog-q", "insurence")
    page.wait_for_selector(".empty .suggestion")
    page.locator(".empty .suggestion").first.click()
    page.wait_for_selector("#search-results article.post")
    assert page.input_value("#blog-q") == "insurance"
    browser.close()


def test_matches_hidden_by_topic_are_offered(pw, base):
    browser, page, _ = _blog(pw, base)
    page.locator('.chip[data-topic="Rentals"]').click()
    page.wait_for_selector("#results-h")
    page.fill("#blog-q", "dui")
    page.wait_for_selector(".empty .suggestion")
    btn = page.locator(".empty .suggestion", has_text="all topics")
    assert btn.count() == 1
    btn.click()
    page.wait_for_selector("#search-results article.post")
    assert page.locator('.chip.is-on[data-topic=""]').count() == 1
    browser.close()


def test_pagination_and_back(pw, base):
    browser, page, _ = _blog(pw, base)
    page.locator('.chip[data-topic="Coverages"]').click()
    page.wait_for_selector(".results-range")
    assert page.inner_text(".results-range").startswith("Showing 1 to 12 of")
    page.locator('#search-results .pagination button[data-page="2"]').click()
    page.wait_for_function("document.querySelector('.results-range').textContent.startsWith('Showing 13 to 24')")
    assert "page=2" in page.url and "topic=Coverages" in page.url
    assert page.evaluate("document.activeElement.id") == "results-h"
    page.go_back()
    page.wait_for_function("document.querySelector('.results-range').textContent.startsWith('Showing 1 to 12')")
    page.go_back()
    page.wait_for_function("!document.getElementById('default-view').hidden")
    browser.close()


def test_reload_restores_query(pw, base):
    browser, page, _ = _blog(pw, base, BLOG + "?q=sr22")
    page.wait_for_selector("#search-results article.post")
    assert page.input_value("#blog-q") == "sr22"
    browser.close()


def test_index_failure_falls_back_to_wordpress_search(pw, base):
    browser = pw.chromium.launch()
    page = browser.new_page()
    page.route("**/assets/data/posts-index.json", lambda r: r.abort())
    seen = []
    page.route("https://www.insureonthespot.com/**", lambda r: (seen.append(r.request.url), r.abort()))
    page.goto(base + BLOG, wait_until="load")
    page.wait_for_selector("[data-blog-search][data-ready]", state="attached")
    page.fill("#blog-q", "sr22")
    page.wait_for_selector(".notice")
    page.press("#blog-q", "Enter")
    page.wait_for_timeout(800)
    assert any(u.startswith("https://www.insureonthespot.com/?s=sr22") for u in seen), seen
    browser.close()


@pytest.mark.parametrize("query", ["sr22", "zzqxv"])
def test_axe_on_search_states(pw, base, query):
    browser, page, _ = _blog(pw, base, width=390)
    page.fill("#blog-q", query)
    page.wait_for_selector("#results-h")
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 0, overflow
    page.add_script_tag(content=AXE)
    res = page.evaluate("axe.run(document, {resultTypes: ['violations']})")
    assert not res["violations"], [(v["id"], len(v["nodes"])) for v in res["violations"]]
    browser.close()


def test_typing_before_search_script_loads(pw, base):
    browser = pw.chromium.launch()
    page = browser.new_page()
    def slow(route):
        time.sleep(1.0)
        route.continue_()
    page.route("**/assets/js/blog.js*", slow)
    page.goto(base + BLOG, wait_until="domcontentloaded")
    page.fill("#blog-q", "sr22")  # typed before blog.js has loaded
    page.wait_for_function("(document.getElementById('results-h') || {}).textContent?.includes('sr22')", timeout=10000)
    browser.close()
