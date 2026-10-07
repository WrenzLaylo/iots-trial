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
                    page.wait_for_timeout(1500)
                    page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(800)
                page.screenshot(path=OUT / f"{name}-{view}.png", full_page=True)
                page.close()
            ctx.close()
        browser.close()
    print(sorted(f.name for f in OUT.glob("*.png")))


if __name__ == "__main__":
    main(sys.argv[1].rstrip("/"))
