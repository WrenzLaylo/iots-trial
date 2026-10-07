"""Screen-sized screenshots for the submission (what you'd actually see, not one long full-page scroll).

Two shots per page and device: the top of the page, then the section that shows the main improvement.
Desktop 1440x900, iPhone 15 Pro 393x852 at 3x.

Usage: py -3.11 qa/shoot_screens.py https://iots-trial.vercel.app deliverables/submit-v3/screenshots
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

DAYTIME = datetime(2026, 10, 7, 15, 30, tzinfo=timezone.utc)  # Wed 10:30 AM in Chicago, so branches show "Open"
VIEWS = {
    "desktop": dict(viewport={"width": 1440, "height": 900}, device_scale_factor=1),
    "mobile": dict(viewport={"width": 393, "height": 852}, device_scale_factor=3, is_mobile=True, has_touch=True,
                   user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"),
}


def scroll_to(page, selector, offset):
    page.evaluate("([s, o]) => window.scrollTo(0, document.querySelector(s).getBoundingClientRect().top + scrollY - o)", [selector, offset])
    page.wait_for_timeout(700)


def blog_search(page, view):
    page.wait_for_selector("[data-blog-search][data-ready]", state="attached")
    page.fill("#blog-q", "sr22")
    page.wait_for_selector(".results-range")
    scroll_to(page, "#blog-q", 84 if view == "desktop" else 72)  # search box just under the sticky header


def locations_cards(page, view):
    scroll_to(page, "#main h2", 96 if view == "desktop" else 76)
    if view == "desktop":
        page.wait_for_selector(".leaflet-marker-icon", timeout=20000)
    page.wait_for_timeout(1200)  # let map tiles fade in


def contact_sections(page, view):
    scroll_to(page, "#main h2", 100 if view == "desktop" else 80)


SHOTS = [
    ("blog", "/customer-service/blog/", [("1-top", None), ("2-search", blog_search)]),
    ("locations", "/locations/", [("1-top", None), ("2-branches", locations_cards)]),
    ("contact", "/contact/", [("1-top", None), ("2-hours-and-offices", contact_sections)]),
]


def main(base, out):
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for view, opts in VIEWS.items():
            ctx = browser.new_context(**opts)
            for name, path, shots in SHOTS:
                for suffix, prepare in shots:
                    page = ctx.new_page()
                    page.clock.install(time=DAYTIME)
                    page.clock.resume()
                    page.goto(base + path, wait_until="load")
                    page.wait_for_timeout(600)
                    if prepare:
                        prepare(page, view)
                    page.screenshot(path=out / f"{name}-{view}-{suffix}.png")
                    page.close()
            ctx.close()
        browser.close()
    print(sorted(f.name for f in out.glob("*.png")))


if __name__ == "__main__":
    main(sys.argv[1].rstrip("/"), Path(sys.argv[2]))
