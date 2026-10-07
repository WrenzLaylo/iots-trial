"""Captioned walkthrough video of the preview (Playwright screen recording + ffmpeg).

Usage: py -3.11 qa/walkthrough.py [base-url] [out.mp4]
"""
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://iots-trial.vercel.app").rstrip("/")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "deliverables" / "walkthrough-v2.mp4"
TMP = ROOT / "qa" / "out" / "video"
DAYTIME = datetime(2026, 10, 7, 15, 30, tzinfo=timezone.utc)  # Wed 10:30 AM in Chicago: branches show "Open"

OVERLAY = """
(() => {
  const install = () => {
    if (document.getElementById('wt-cap')) return;
    const small = innerWidth < 600;
    const cap = document.createElement('div');
    cap.id = 'wt-cap';
    Object.assign(cap.style, { position: 'fixed', left: '50%', bottom: small ? '18px' : '28px', transform: 'translateX(-50%)',
      zIndex: 2147483647, width: small ? '88%' : 'auto', maxWidth: '82%', padding: small ? '10px 14px' : '14px 22px',
      borderRadius: '14px', background: 'rgba(0,24,38,.93)', color: '#fff', textAlign: 'center', opacity: '0',
      font: `600 ${small ? 15 : 22}px/1.35 Figtree, system-ui, sans-serif`, boxShadow: '0 12px 30px rgba(0,0,0,.35)',
      transition: 'opacity .25s', pointerEvents: 'none' });
    document.body.appendChild(cap);
    const dot = document.createElement('div');
    dot.id = 'wt-dot';
    Object.assign(dot.style, { position: 'fixed', left: '-40px', top: '-40px', width: '22px', height: '22px', margin: '-11px 0 0 -11px',
      borderRadius: '50%', background: 'rgba(255,205,60,.85)', border: '2px solid #002d45', zIndex: 2147483647,
      pointerEvents: 'none', transition: 'transform .12s' });
    document.body.appendChild(dot);
    addEventListener('mousemove', (e) => { dot.style.left = e.clientX + 'px'; dot.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', () => { dot.style.transform = 'scale(.65)'; }, true);
    addEventListener('mouseup', () => { dot.style.transform = ''; }, true);
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', install); else install();
})();
"""


def caption(page, text, hold=2.5):
    page.evaluate(OVERLAY)
    page.evaluate("t => { const c = document.getElementById('wt-cap'); c.textContent = t; c.style.opacity = t ? '1' : '0'; }", text)
    page.wait_for_timeout(int(hold * 1000))


def glide(page, locator, click=True):
    locator.scroll_into_view_if_needed()
    box = locator.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=28)
    page.wait_for_timeout(250)
    if click:
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


def scroll_to(page, y, wait=1200):
    page.evaluate("y => window.scrollTo({ top: y, behavior: 'smooth' })", y)
    page.wait_for_timeout(wait)


def type_slowly(page, text):
    page.keyboard.type(text, delay=170)


def desktop(pw, video_dir):
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, record_video_dir=str(video_dir),
                              record_video_size={"width": 1280, "height": 800})
    ctx.add_init_script(OVERLAY)
    page = ctx.new_page()
    page.clock.install(time=DAYTIME)
    page.clock.resume()
    page.goto(BASE + "/customer-service/blog/", wait_until="load")
    page.wait_for_selector("[data-blog-search][data-ready]", state="attached")
    caption(page, "Insure On The Spot: blog, locations and contact pages, rebuilt as a clickable preview", 3.5)
    caption(page, "Their 594 posts have no images, so each topic gets its own cover art and a reading time", 1.2)
    scroll_to(page, 640, 2600)
    scroll_to(page, 0, 1200)

    caption(page, "Search shows results as you type, across all 594 guides", 0.6)
    glide(page, page.locator("#blog-q"))
    type_slowly(page, "sr22")
    page.wait_for_timeout(2600)
    caption(page, "It ignores accents and punctuation: \"sr22\" finds \"SR-22\", \"que\" finds \"Qué\"", 0.6)
    page.fill("#blog-q", "")
    type_slowly(page, "que pasa")
    page.wait_for_timeout(2600)

    caption(page, "No dead ends: a typo gets a suggestion, tips, popular topics and a phone number", 0.6)
    page.fill("#blog-q", "")
    type_slowly(page, "insurence")
    page.wait_for_selector(".empty .suggestion")
    page.wait_for_timeout(2800)
    glide(page, page.locator(".empty .suggestion").first)
    caption(page, "One click and the search is fixed", 2.6)

    glide(page, page.locator("[data-clear]"))
    caption(page, "Topics filter instantly, with real pagination", 0.6)
    glide(page, page.locator('.chip[data-topic="Coverages"]'))
    page.wait_for_selector(".results-range")
    page.wait_for_timeout(1800)
    glide(page, page.locator('#search-results .pagination button[data-page="2"]'))
    page.wait_for_timeout(2200)
    caption(page, "Back works too, because the search state lives in the URL", 0.8)
    page.go_back()
    page.wait_for_timeout(2400)

    page.goto(BASE + "/locations/", wait_until="load")
    caption(page, "Locations: every branch is tap-to-call, with its hours and a live open/closed label in Chicago time", 4.5)
    scroll_to(page, 420, 1800)
    page.locator(".map-panel").scroll_into_view_if_needed()
    page.wait_for_selector(".leaflet-marker-icon", timeout=15000)
    caption(page, "The map only loads when you reach it. If it can't, a Google Maps link is always there", 3.6)

    page.goto(BASE + "/contact/", wait_until="load")
    caption(page, "Contact: one tap to call or get a quote, then phone hours, quick links and every branch", 1.0)
    glide(page, page.locator('.page-head a.btn-cta'), click=False)
    page.wait_for_timeout(2600)
    scroll_to(page, 520, 1600)
    caption(page, "No contact form yet, on purpose: open question for you on who would answer it", 3.6)
    scroll_to(page, 0, 1000)
    caption(page, "Lighthouse mobile: 97-100 performance and 100 accessibility (the live pages score 26-27 and 87-95)", 4.5)
    video = page.video
    ctx.close()
    browser.close()
    return Path(video.path())


def phone(pw, video_dir):
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 393, "height": 852}, is_mobile=True, has_touch=True, device_scale_factor=2,
                              record_video_dir=str(video_dir), record_video_size={"width": 393, "height": 852},
                              user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
    ctx.add_init_script(OVERLAY)
    page = ctx.new_page()
    page.clock.install(time=DAYTIME)
    page.clock.resume()
    page.goto(BASE + "/customer-service/blog/", wait_until="load")
    page.wait_for_selector("[data-blog-search][data-ready]", state="attached")
    caption(page, "On a phone: the same search, built for thumbs", 0.6)
    page.locator("#blog-q").tap()
    type_slowly(page, "dui")
    page.wait_for_timeout(2600)
    page.goto(BASE + "/locations/", wait_until="load")
    caption(page, "Full-width Call buttons for every branch", 0.6)
    scroll_to(page, 260, 2400)
    scroll_to(page, 900, 2200)
    scroll_to(page, 0, 900)
    page.goto(BASE + "/contact/", wait_until="load")
    caption(page, "Contact: Call and Get Free Quote, full width, Call on top", 2.8)
    caption(page, "Menu, call button and quote box are always one tap away", 0.6)
    page.locator("[data-menu-toggle]").tap()
    page.wait_for_timeout(2200)
    caption(page, "Preview: iots-trial.vercel.app", 2.6)
    video = page.video
    ctx.close()
    browser.close()
    return Path(video.path())


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    for f in TMP.glob("*.webm"):
        f.unlink()
    with sync_playwright() as pw:
        d = desktop(pw, TMP)
        m = phone(pw, TMP)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    flt = ("[0:v]scale=1280:800,setsar=1,fps=30[a];"
           "[1:v]scale=-2:760,pad=1280:800:(ow-iw)/2:(oh-ih)/2:color=0x002d45,setsar=1,fps=30[b];"
           "[a][b]concat=n=2:v=1:a=0[v]")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(d), "-i", str(m), "-filter_complex", flt, "-map", "[v]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)],
                   check=True)
    print(OUT, round(OUT.stat().st_size / 1024 / 1024, 1), "MB")


if __name__ == "__main__":
    main()
