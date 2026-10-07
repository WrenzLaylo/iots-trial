"""Render templates + data into site/. Run: py -3.11 build/build.py"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote_plus

from jinja2 import Environment, FileSystemLoader, StrictUndefined

import jsonld

ROOT = Path(__file__).resolve().parent.parent
DATA, TPL, STATIC, OUT = ROOT / "data", ROOT / "templates", ROOT / "static", ROOT / "site"
PROD = jsonld.PROD
DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DAY_ABBR = {"mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu", "fri": "Fri", "sat": "Sat", "sun": "Sun"}
PER_PAGE, BLOG_PAGES = 12, 3
HIDDEN_CATEGORIES = {"uncategorized"}


def fmt_time(hhmm: str) -> str:
    h, m = map(int, hhmm.split(":"))
    return f"{h % 12 or 12}:{m:02d} {'PM' if h >= 12 else 'AM'}"


def _row(days, span):
    label = DAY_ABBR[days[0]] if len(days) == 1 else f"{DAY_ABBR[days[0]]}-{DAY_ABBR[days[-1]]}"
    return {"label": label, "days": " ".join(days), "text": f"{fmt_time(span[0])} to {fmt_time(span[1])}"}


def group_hours(hours: dict) -> list[dict]:
    rows, run = [], []
    for day in DAY_KEYS:
        span = hours.get(day)
        if span and run and hours[run[-1]] == span:
            run.append(day)
            continue
        if run:
            rows.append(_row(run, hours[run[0]]))
        run = [day] if span else []
    if run:
        rows.append(_row(run, hours[run[0]]))
    return rows


def clean_excerpt(raw: str, limit: int = 170) -> str:
    text = re.sub(r"<a\b[^>]*>.*?</a>", " ", raw, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text)).replace("\xa0", " ")
    text = re.sub(r"\[(?:…|\.\.\.)\]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    truncated = text.endswith("…") or text.endswith("...")
    text = text.rstrip("…").rstrip(".").rstrip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(",;:")
        truncated = True
    return text + ("…" if truncated else "")


def directions_url(b: dict) -> str:
    return "https://www.google.com/maps/dir/?api=1&destination=" + quote_plus(f"{b['street']}, {b['city']}, {b['state']} {b['zip']}")


def paginate(items: list, per_page: int, pages: int) -> list[list]:
    return [items[i * per_page:(i + 1) * per_page] for i in range(pages)]


def _json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _icons() -> dict:
    out = {}
    for svg in (STATIC / "icons").glob("*.svg"):
        body = svg.read_text(encoding="utf-8")
        body = re.sub(r'\s(width|height)="[^"]*"', "", body)
        body = body.replace('fill="#000000"', 'fill="currentColor"')
        body = body.replace("<svg ", '<svg class="icon" aria-hidden="true" focusable="false" ', 1)
        out[svg.stem] = body
    return out


def load_context() -> dict:
    site, br = _json("site.json"), _json("branches.json")
    links = site["links"]
    resolve = lambda items: [{"label": i["label"], "href": i.get("href") or links[i["key"]]} for i in items]
    branches = [b | {"hours_rows": group_hours(b["hours"]), "directions": directions_url(b)} for b in br["branches"]]
    departments = [d | {"hours_rows": group_hours(d["hours"])} for d in br["departments"]]
    try:
        build_id = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        build_id = "dev"
    return {
        "links": links, "nav_top": resolve(site["nav_top"]), "nav_main": resolve(site["nav_main"]),
        "footer": [{"heading": c["heading"], "items": resolve(c["items"])} for c in site["footer"]],
        "legal": resolve(site["legal"]), "icons": _icons(), "images": _json("images.json"),
        "branches": branches, "departments": departments, "holiday_note": br["holiday_note"],
        "main_phone": br["main_phone"], "main_tel": br["main_tel"], "build_id": build_id,
    }


def _env() -> Environment:
    return Environment(loader=FileSystemLoader(TPL), autoescape=True, undefined=StrictUndefined,
                       trim_blocks=True, lstrip_blocks=True)


def _write(out: Path, rel: str, content: str) -> Path:
    path = out / rel / "index.html" if rel else out / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def pages(ctx: dict) -> list[tuple[str, str, dict]]:
    """(template, output dir relative to site/, page dict). Extended by Tasks 4-6."""
    return [("index.html", "", {"slug": "home", "path": "/", "title": "Insure On The Spot preview: 3 rebuilt pages",
                                "description": "Trial task preview for Vela: rebuilt blog, locations and contact pages for Insure On The Spot, with an audit of what was fixed and why.",
                                "jsonld": [], "crumbs": []})]


def render_all(out: Path = OUT) -> list[Path]:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(STATIC, out / "assets", ignore=shutil.ignore_patterns("icons"))
    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    ctx, env = load_context(), _env()
    env.globals.update(ctx)  # globals (not render kwargs) so macros imported from _macros.html can see them
    written = []
    for template, rel, page in pages(ctx):
        extra = page.pop("extra", {})
        html_out = env.get_template(template).render(**extra, page=page)
        written.append(_write(out, rel, html_out))
    return written


if __name__ == "__main__":
    for p in render_all():
        print(p.relative_to(ROOT))
