"""Dev helper: screenshot a built page. Usage: py -3.11 qa/snap.py /path/ name [scroll-selector]"""
import functools, http.server, sys, threading
from playwright.sync_api import sync_playwright
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8766), functools.partial(Quiet, directory="site"))
threading.Thread(target=srv.serve_forever, daemon=True).start()
path, name = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch()
    for view, opts in {"d": dict(viewport={"width": 1440, "height": 900}), "m": dict(viewport={"width": 393, "height": 852}, is_mobile=True, has_touch=True)}.items():
        pg = b.new_page(**opts); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"http://127.0.0.1:8766{path}", wait_until="load")
        if len(sys.argv) > 3:
            pg.locator(sys.argv[3]).scroll_into_view_if_needed(); pg.wait_for_timeout(2500); pg.evaluate("scrollTo(0,0)")
        pg.wait_for_timeout(500)
        pg.screenshot(path=f"qa/out/{name}-{view}.png", full_page=True)
        print(view, "overflow:", pg.evaluate("document.documentElement.scrollWidth - innerWidth"), "errors:", errs)
    b.close()
srv.shutdown()
