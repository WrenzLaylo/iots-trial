"""Walkthrough video to voice over: a Playwright recording with the script burned in as captions,
BEFORE / AFTER badges, highlight boxes on the live site and the rebuild, two iPhones, and title slides.

Usage: py -3.11 qa/voiceover.py [base-url] [out.mp4]
Also writes <out>.txt: every caption with the time it appears, to rehearse with.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://iots-trial.vercel.app").rstrip("/")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "deliverables" / "walkthrough-voiceover.mp4"
TMP = ROOT / "qa" / "out" / "voiceover"
LIVE = "https://www.insureonthespot.com"
REPO = "https://github.com/WrenzLaylo/iots-trial"
DAYTIME = datetime(2026, 10, 7, 15, 30, tzinfo=timezone.utc)  # Wed 10:30 AM in Chicago: branches show "Open"
W, H = 1280, 720
WORDS_PER_SEC = 2.3  # a calm reading pace: each caption stays up at least this long

OVERLAY = """
(() => {
  if (window.__wt) return;
  const api = window.__wt = {};
  const st = (el, s) => Object.assign(el.style, s);
  const FONT = "'Segoe UI', system-ui, sans-serif";
  const install = () => {
    const dot = document.createElement('div');
    st(dot, { position: 'fixed', left: '-40px', top: '-40px', width: '22px', height: '22px', margin: '-11px 0 0 -11px',
      borderRadius: '50%', background: 'rgba(255,205,60,.85)', border: '2px solid #002d45', zIndex: 2147483647,
      pointerEvents: 'none', transition: 'transform .12s' });
    document.body.appendChild(dot);
    addEventListener('mousemove', (e) => { dot.style.left = e.clientX + 'px'; dot.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', () => { dot.style.transform = 'scale(.65)'; }, true);
    addEventListener('mouseup', () => { dot.style.transform = ''; }, true);
    if (window !== window.top) return;  // inside the iPhone frames: cursor only

    const wrap = document.createElement('div');
    st(wrap, { position: 'fixed', left: '50%', bottom: '20px', transform: 'translateX(-50%)', zIndex: 2147483647, width: '86%',
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '7px', pointerEvents: 'none' });
    const badge = document.createElement('div');
    st(badge, { padding: '5px 14px', borderRadius: '999px', color: '#fff', font: `700 14px/1.3 ${FONT}`, letterSpacing: '.06em',
      display: 'none', boxShadow: '0 4px 14px rgba(0,0,0,.3)' });
    const cap = document.createElement('div');
    st(cap, { padding: '12px 22px', borderRadius: '14px', background: 'rgba(0,24,38,.94)', color: '#fff', textAlign: 'center',
      font: `600 23px/1.38 ${FONT}`, boxShadow: '0 12px 30px rgba(0,0,0,.35)', display: 'none' });
    wrap.append(badge, cap);
    document.body.appendChild(wrap);

    const layer = document.createElement('div');
    st(layer, { position: 'absolute', left: '0', top: '0', width: '0', height: '0', zIndex: 2147483646, pointerEvents: 'none' });
    document.body.appendChild(layer);

    api.cap = (t) => { cap.textContent = t; cap.style.display = t ? 'block' : 'none'; };
    api.badge = (kind) => {
      const k = { before: ['BEFORE: THE LIVE SITE TODAY', '#b42318'], after: ['AFTER: MY REBUILD', '#067647'] }[kind];
      badge.style.display = k ? 'block' : 'none';
      if (k) { badge.textContent = k[0]; badge.style.background = k[1]; }
    };
    api.unmark = () => { layer.innerHTML = ''; };
    api.mark = (els, label, kind, textRect, side) => {
      const color = kind === 'good' ? '#067647' : '#d92d20';
      els.filter(Boolean).forEach((el, i) => {
        let r = el.getBoundingClientRect();
        if (textRect) { const rg = document.createRange(); rg.selectNodeContents(el); r = rg.getBoundingClientRect(); }
        const box = document.createElement('div');
        st(box, { position: 'absolute', left: (r.left + scrollX - 7) + 'px', top: (r.top + scrollY - 5) + 'px',
          width: (r.width + 14) + 'px', height: (r.height + 10) + 'px', border: `3px solid ${color}`, borderRadius: '9px',
          boxShadow: `0 0 0 5px ${color}2e`, opacity: '0', transition: 'opacity .3s', boxSizing: 'border-box' });
        layer.appendChild(box);
        if (i === 0 && label) {
          const tag = document.createElement('div');
          tag.textContent = label;
          const pos = side === 'right' ? { left: 'calc(100% + 12px)', top: '50%', transform: 'translateY(-50%)' }
                    : side === 'below' ? { left: '-3px', top: 'calc(100% + 8px)' }
                    : { left: '-3px', bottom: 'calc(100% + 8px)' };
          st(tag, Object.assign({ position: 'absolute', whiteSpace: 'nowrap', background: color, color: '#fff',
            font: `700 16px/1.2 ${FONT}`, padding: '7px 12px', borderRadius: '7px', boxShadow: '0 6px 16px rgba(0,0,0,.25)' }, pos));
          box.appendChild(tag);
        }
        requestAnimationFrame(() => requestAnimationFrame(() => { box.style.opacity = '1'; }));
      });
    };
    api.ok = true;
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', install); else install();
})();
"""

# ---------- slides (served on the preview's own origin so the Figtree font and iframes load) ----------
SLIDE_CSS = """
@font-face{font-family:Figtree;src:url(/assets/fonts/figtree-latin.woff2) format("woff2");font-weight:300 900}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{font-family:Figtree,system-ui,sans-serif;background:radial-gradient(1200px 600px at 80% -10%,#0a4a6e 0,#002d45 55%);color:#fff;
  display:flex;align-items:center;justify-content:center;padding:40px 80px 130px}
.eyebrow{color:#ffcd3c;font-weight:700;font-size:19px;letter-spacing:.02em;margin:0 0 14px}
h1{font-size:52px;line-height:1.08;margin:0 0 18px;font-weight:800;letter-spacing:-.01em}
h2{font-size:42px;line-height:1.1;margin:0 0 28px;font-weight:800}
.by{font-size:22px;color:#cfe3ef;margin:0}
.logo{background:#fff;border-radius:16px;padding:14px 18px;display:inline-block;margin-bottom:26px}
.logo img{display:block;height:54px;width:auto}
.stats{display:flex;gap:18px;margin-top:34px}
.stat{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);border-radius:16px;padding:16px 22px;min-width:200px}
.stat b{display:block;font-size:40px;color:#ffcd3c;line-height:1}.stat span{font-size:17px;color:#d8e8f2}
ul.checks{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:16px 40px}
ul.checks li{font-size:24px;display:flex;gap:14px;align-items:center}
ul.checks li:before{content:"";flex:none;width:30px;height:30px;border-radius:50%;background:#12b76a url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12.5l4.5 4.5L19 7.5'/%3E%3C/svg%3E") center/18px no-repeat}
ul.checks small{color:#a9c6d8;font-size:18px}
table{border-collapse:separate;border-spacing:0 10px;font-size:24px;width:100%}
th{font-size:16px;text-transform:uppercase;letter-spacing:.08em;color:#a9c6d8;text-align:left;font-weight:700;padding:0 18px}
td{background:rgba(255,255,255,.07);padding:13px 18px}td:first-child{border-radius:12px 0 0 12px;font-weight:700}
td:last-child{border-radius:0 12px 12px 0}
.bad{color:#ff9c8f;font-weight:700}.good{color:#5ce0a0;font-weight:800}
.note{color:#a9c6d8;font-size:17px;margin-top:14px}
.phones{display:flex;gap:90px;align-items:flex-start;justify-content:center;--s:.64}
.ph{display:flex;flex-direction:column;align-items:center;gap:12px}
.ph b{font-size:19px;color:#ffcd3c}
.frame{background:#0d0f12;border-radius:44px;padding:9px;box-shadow:0 0 0 2px #3b4148,0 26px 60px rgba(0,0,0,.5)}
.screen{width:calc(393px * var(--s));height:calc(800px * var(--s));border-radius:36px;overflow:hidden;background:#fff;position:relative}
.status{height:calc(54px * var(--s));display:flex;align-items:center;justify-content:space-between;padding:0 22px;
  font:600 12px/1 system-ui,sans-serif;color:#111;background:#fff}
.island{position:absolute;top:calc(11px * var(--s));left:50%;transform:translateX(-50%);width:calc(124px * var(--s));
  height:calc(35px * var(--s));background:#000;border-radius:999px;z-index:2}
.screen iframe{width:393px;height:746px;border:0;display:block;transform:scale(var(--s));transform-origin:0 0}
.links{font-size:26px;line-height:1.9;margin-top:6px}.links span{color:#a9c6d8;display:inline-block;min-width:150px}
"""


def slide(body):
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{SLIDE_CSS}</style></head><body>{body}</body></html>'


def phone(name, src):
    return (f'<div class="ph"><b>{name}</b><div class="frame"><div class="screen"><div class="island"></div>'
            f'<div class="status"><span>10:30</span><span>5G</span></div>'
            f'<iframe name="{name.lower()}" src="{src}" title="{name} on an iPhone"></iframe></div></div></div>')


SLIDES = {
    "title": slide('<main><div class="logo"><img src="/assets/img/logo.png" alt=""></div>'
                   '<p class="eyebrow">Technical SEO Developer trial for Vela</p>'
                   '<h1>Blog, Locations and Contact:<br>rebuilt and improved</h1><p class="by">Wrenz Laylo</p>'
                   '<div class="stats"><div class="stat"><b>26</b><span>issues found in the audit</span></div>'
                   '<div class="stat"><b>3</b><span>pages rebuilt</span></div>'
                   '<div class="stat"><b>594</b><span>blog posts, all searchable</span></div></div></main>'),
    "phones": slide(f'<div class="phones">{phone("Locations", "/locations/")}{phone("Contact", "/contact/")}</div>'),
    "seo": slide('<main><p class="eyebrow">Behind the scenes, on all three pages</p><h2>SEO basics</h2><ul class="checks">'
                 '<li><span>Meta descriptions <small>(none before)</small></span></li><li>One real H1 per page</li>'
                 '<li>Headings in order</li><li>Alt text on every image</li><li>Structured data for each office</li>'
                 '<li>Spanish content marked as Spanish</li></ul></main>'),
    "lighthouse": slide('<main style="width:900px"><p class="eyebrow">Lighthouse, mobile</p><h2>Live site vs my rebuild</h2>'
                        '<table><tr><th></th><th>Live site</th><th>Rebuild</th></tr>'
                        '<tr><td>Performance</td><td class="bad">26 to 27</td><td class="good">97 to 100</td></tr>'
                        '<tr><td>Accessibility</td><td class="bad">87 to 95</td><td class="good">100</td></tr>'
                        '<tr><td>Best practices</td><td class="bad">54</td><td class="good">100</td></tr>'
                        '<tr><td>Main content shows in</td><td class="bad">16 to 20 s</td><td class="good">1 to 2 s</td></tr></table>'
                        '<p class="note">Part of the gap: the preview doesn\'t load their marketing tags.</p></main>'),
    "thanks": slide('<main><div class="logo"><img src="/assets/img/logo.png" alt=""></div><h2>Thanks for watching</h2>'
                    '<div class="links"><div><span>Preview</span>iots-trial.vercel.app</div>'
                    '<div><span>Code</span>github.com/WrenzLaylo/iots-trial</div>'
                    '<div><span>In the zip</span>the 26-item audit, QA results, screenshots</div></div></main>'),
}

# ---------- element finders (JS expressions that return arrays of elements) ----------
LIVE_PHONES = r"[...document.querySelectorAll('p')].filter(e => e.children.length === 0 && /^\(\d{3}\) \d{3}-\d{4}$/.test(e.textContent.trim()))"
LIVE_HOURS = "[...document.querySelectorAll('a')].filter(a => /See Hours/.test(a.textContent) && a.getBoundingClientRect().width > 0)"
LIVE_H1 = "[...document.querySelectorAll('h1')].filter(h => h.getBoundingClientRect().width > 0).slice(0, 1)"
LIVE_DUP = ("(() => { const h = [...document.querySelectorAll('h1')].find(h => h.getBoundingClientRect().width > 0);"
            " const t = h.textContent.trim(); return [[...document.querySelectorAll('h2, h3')].find(x => x.textContent.includes(t))]; })()")
LIVE_OLDER = "[...document.querySelectorAll('a')].filter(a => /Older Articles/.test(a.textContent) && a.getBoundingClientRect().width > 0)"


def q(sel):
    return f"[...document.querySelectorAll({json.dumps(sel)})].slice(0, 1)"


class Narrator:
    """Shows one caption at a time and keeps it up long enough to read aloud; logs when each one appears."""

    def __init__(self, page):
        self.page, self.t0, self.until, self.text, self.kind, self.lines = page, time.monotonic(), 0.0, "", "", []

    def wait(self, ms):
        self.page.wait_for_timeout(ms)

    def hold(self):
        left = self.until - time.monotonic()
        if left > 0:
            self.wait(int(left * 1000))

    def go(self, url, badge="", lead=0.0):
        # lead: start a slow load this many seconds early; the old page (and its caption) stays up until the new one paints
        self.until -= lead
        self.hold()
        self.text, self.kind = "", badge
        self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        self.page.wait_for_function("() => window.__wt && window.__wt.ok", timeout=30000)
        self.page.evaluate("document.fonts.ready.then(() => 1)")
        self.page.evaluate("k => __wt.badge(k)", badge)

    def say(self, text):
        self.hold()
        self.text = text
        self.page.evaluate("t => __wt.cap(t)", text)
        now = time.monotonic()
        self.lines.append((now - self.t0, text))
        self.until = now + max(3.0, len(text.split()) / WORDS_PER_SEC + 1.0)

    def mark(self, finder, label="", kind="bad", text=False, side="top"):
        self.page.evaluate(f"([l, k, t, s]) => __wt.mark({finder}, l, k, t, s)", [label, kind, text, side])

    def unmark(self):
        self.page.evaluate("__wt.unmark()")

    def scroll(self, y, ms=1400):
        self.page.evaluate("y => window.scrollTo({ top: y, behavior: 'smooth' })", y)
        self.wait(ms)

    def scroll_to(self, finder, offset=120, ms=1600):
        y = self.page.evaluate(f"() => {{ const e = ({finder})[0]; return e.getBoundingClientRect().top + scrollY; }}")
        self.scroll(max(0, y - offset), ms)

    def point(self, finder, text=False, click=False):
        r = self.page.evaluate(f"""t => {{ const e = ({finder})[0]; let r = e.getBoundingClientRect();
            if (t) {{ const g = document.createRange(); g.selectNodeContents(e); r = g.getBoundingClientRect(); }}
            return {{ x: r.left + r.width / 2, y: r.top + r.height / 2 }}; }}""", text)
        self.page.mouse.move(r["x"], r["y"], steps=26)
        self.wait(250)
        if click:
            self.page.mouse.click(r["x"], r["y"])

    def type(self, text):
        self.page.keyboard.type(text, delay=170)


def record(pw):
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": W, "height": H}, record_video_dir=str(TMP), record_video_size={"width": W, "height": H})
    ctx.add_init_script(OVERLAY)
    ctx.route(f"{BASE}/__slide/*", lambda route: route.fulfill(status=200, content_type="text/html; charset=utf-8",
                                                               body=SLIDES[route.request.url.rsplit("/", 1)[1]]))
    page = ctx.new_page()
    page.clock.install(time=DAYTIME)
    page.clock.resume()
    n = Narrator(page)

    # 1. Intro
    n.go(f"{BASE}/__slide/title")
    n.wait(1200)
    n.say("Hi, I'm Wrenz. This is my rebuild of three Insure On The Spot pages: Locations, Contact and the blog.")
    n.say("Before building, I audited the live pages and found 26 issues. Here are the biggest ones and what I changed.")

    # 2. Locations: live, then the rebuild
    n.go(f"{LIVE}/locations/", badge="before", lead=2.5)
    n.wait(700)
    n.say("On the live page, the branch phone numbers are plain text, so on a phone you can't tap to call.")
    n.scroll_to(LIVE_PHONES, 150)
    n.mark(LIVE_PHONES, "Plain text: can't tap to call", text=True, side="right")
    n.point(LIVE_PHONES, text=True)
    n.say("And the hours aren't here. You have to open each branch's own page to find them, and every branch has different hours.")
    n.unmark()
    n.mark(LIVE_HOURS, "Hours: on 4 separate pages", text=True, side="right")
    n.point(LIVE_HOURS, text=True)

    n.go(f"{BASE}/locations/", badge="after")
    n.say("In my version, every branch has a Call button, the hours are right on the card with today in bold,")
    n.scroll_to(q(".card.branch"), 90)
    n.mark(q(".card.branch .call-btn"), "Tap to call", kind="good", side="right")
    n.point(q(".card.branch .call-btn"))
    n.wait(1200)
    n.mark(q(".card.branch .hours"), "Hours on the card", kind="good", side="right")
    n.point(q(".card.branch .hours"))
    n.say("and there's a live open or closed label in Chicago time. Holidays aren't in their data, so each card says to call and confirm.")
    n.unmark()
    n.mark(q(".card.branch .status"), "Live: open or closed, Chicago time", kind="good", side="right")
    n.point(q(".card.branch .status"))
    n.say("The map only loads when you scroll to it, so it doesn't slow the page down. And there's always a Google Maps link.")
    n.unmark()
    page.wait_for_selector(".leaflet-marker-icon", timeout=20000)
    n.wait(600)
    n.mark(q(".map-canvas"), "Loads only when you reach it", kind="good")
    n.point(q(".map-canvas"))

    # 3. Contact
    n.go(f"{BASE}/contact/", badge="after")
    n.say("Contact now starts with the two things people come here for: call, or get a quote.")
    n.mark(q(".head-ctas"), "Call or get a quote", kind="good", side="below")
    n.point(q(".head-ctas .btn-cta"))
    n.wait(900)
    n.point(q(".head-ctas .btn-outline"))
    n.say("Below that are the phone hours for customer service and sales, shortcuts for payments, claims and roadside help, and all four offices.")
    n.unmark()
    n.scroll(420, 2600)
    n.scroll(820, 2600)
    n.say("On the live page, that headline was baked into the hero image, so I used their staff photo and made the text real, for Google and screen readers.")
    n.scroll(0, 1600)
    n.mark(q(".page-head .eyebrow"), "Real text, not part of the image", kind="good", side="right")
    n.say("I didn't add a contact form on purpose. Someone has to answer it and decide where the leads go, so that's a question for you.")
    n.unmark()

    # 4. Blog: live, then the rebuild
    n.go(f"{LIVE}/customer-service/blog/", badge="before", lead=2.5)
    n.wait(700)
    n.say("On the live blog, the main heading is the title of the latest post,")
    n.mark(LIVE_H1, "The page's main heading (H1)", side="right")
    n.wait(1600)
    n.mark(LIVE_DUP, "The first post: same title", side="right")
    n.say("there's no search, and it shows four posts per page, so there are 149 pages.")
    n.unmark()
    n.scroll_to(LIVE_OLDER, 380, 2200)
    n.mark(LIVE_OLDER, "The only way on: 149 pages", text=True)
    n.point(LIVE_OLDER, text=True)

    n.go(f"{BASE}/customer-service/blog/", badge="after")
    page.wait_for_selector("[data-blog-search][data-ready]", state="attached")
    n.say("Here, the heading is the page title. Each topic has its own cover art and every post shows a reading time, so it's easier to scan.")
    n.mark(q("main h1"), "A real page heading", kind="good", side="right")
    n.wait(2200)
    n.unmark()
    n.scroll(560, 3000)
    n.scroll(0, 1200)
    n.say("Search shows results as you type, across all 594 posts.")
    n.point(q("#blog-q"), click=True)
    n.type("sr22")
    n.wait(900)
    n.scroll(190, 1000)
    n.say("It ignores dashes and accents, so 'sr22' finds 'SR-22'.")
    n.say("If there's a typo or nothing matches, it's not a dead end. You get a suggestion, popular topics and the phone number.")
    page.fill("#blog-q", "")
    n.type("insurence")
    page.wait_for_selector(".empty .suggestion")
    n.wait(2600)
    n.point(q(".empty .suggestion"), click=True)
    n.say("Topics filter instantly, there are real page numbers, and Back works, because the search is saved in the URL.")
    n.point(q("[data-clear]"), click=True)
    n.wait(500)
    n.point(q('.chip[data-topic="Coverages"]'), click=True)
    page.wait_for_selector(".results-range")
    n.wait(1500)
    page.locator('#search-results .pagination button[data-page="2"]').scroll_into_view_if_needed()
    n.point(q('#search-results .pagination button[data-page="2"]'), click=True)
    n.wait(1800)
    page.go_back()
    n.wait(1800)

    # 5. Phones
    n.go(f"{BASE}/__slide/phones", badge="after")
    page.wait_for_function("() => [...document.querySelectorAll('iframe')].every(f => f.contentDocument && f.contentDocument.readyState === 'complete')")
    n.wait(1200)
    n.say("On a phone, every branch has a full-width Call button.")
    loc = page.frame(name="locations")
    loc.evaluate("window.scrollTo({ top: 330, behavior: 'smooth' })")
    n.wait(2200)
    loc.evaluate("window.scrollTo({ top: 760, behavior: 'smooth' })")
    n.say("And Contact puts Call and Get Free Quote right at the top, with the menu one tap away.")
    n.wait(1800)
    page.frame(name="contact").locator("[data-menu-toggle]").click()

    # 6. SEO and speed
    n.go(f"{BASE}/__slide/seo")
    n.say("Behind the scenes, I fixed the SEO basics on all three pages, like meta descriptions, which none of them had.")
    n.say("The Español link and the 45 Spanish posts are now marked as Spanish.")
    n.go(f"{BASE}/__slide/lighthouse")
    n.say("On Lighthouse mobile, performance went from about 26 on the live pages to 97 to 100, and accessibility to 100.")
    n.say("Part of the gap is their marketing tags, which my preview doesn't load, so the live site won't hit these exact numbers.")

    # 7. Testing, code, close
    n.go(REPO, lead=2.5)
    n.wait(600)
    n.say("I tested it in Chrome, Firefox and Safari's engine, with an accessibility scan, keyboard only, JavaScript turned off and slow connections.")
    n.scroll_to(q("article.markdown-body"), 70, 2200)
    n.say("The code is on GitHub, with a pull request for each step.")
    n.scroll(page.evaluate("scrollY") + 380, 2600)
    n.say("I also found a few things outside these pages, like two Google Tag Manager containers loading on every page. Those are in my notes.")
    n.go(f"{BASE}/__slide/thanks")
    n.say("Thanks for watching.")
    n.hold()
    n.wait(1500)

    video = page.video
    ctx.close()
    browser.close()
    return Path(video.path()), n.lines


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    for f in TMP.glob("*.webm"):
        f.unlink()
    with sync_playwright() as pw:
        raw, lines = record(pw)
    trim = max(0.0, lines[0][0] - 1.5)  # drop the blank frames before the title slide
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-ss", f"{trim:.2f}", "-i", str(raw),
                    "-vf", f"scale={W}:{H},fps=30,setsar=1", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)], check=True)
    stamp = lambda s: f"{int(s // 60)}:{int(s % 60):02d}"
    OUT.with_suffix(".txt").write_text("\n".join(f"{stamp(t - trim)}  {text}" for t, text in lines) + "\n", encoding="utf-8")
    print(OUT, round(OUT.stat().st_size / 1024 / 1024, 1), "MB,", len(lines), "captions, last at", stamp(lines[-1][0] - trim))


if __name__ == "__main__":
    main()
