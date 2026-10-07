"""Download their images (-> WebP), Figtree, Phosphor icons and Leaflet into static/."""
import io
import json
import re
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
WP = "https://www.insureonthespot.com/wp-content"

IMAGES = {
    # name: (source url, max width or None to keep as-is)
    "logo.png": (f"{WP}/themes/orbit-media/images/logo.png", None),
    "locations-hero.webp": (f"{WP}/uploads/2019/10/iots-hom-hero.jpg", 1200),
    "contact-photo.webp": (f"{WP}/uploads/2020/01/JP2_1071_web-1536x1024.jpg", 1200),
    "bbb.png": (f"{WP}/uploads/2019/12/BBBLogo.png", 360),  # original is 1411px / 324 KB for a 56px-tall badge
    "favicon.ico": (f"{WP}/themes/orbit-media/favicon.ico", None),
}
ICONS = ["phone", "navigation-arrow", "clock", "storefront", "car", "list", "x", "magnifying-glass",
         "credit-card", "arrows-clockwise", "file-text", "truck", "question", "star", "briefcase",
         "gift", "map-pin", "caret-right"]
LEAFLET = "https://unpkg.com/leaflet@1.9.4/dist"
LEAFLET_FILES = ["leaflet.js", "leaflet.css", "images/marker-icon.png", "images/marker-icon-2x.png", "images/marker-shadow.png"]


def fetch(url, headers=UA):
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.content


def images():
    out = STATIC / "img"
    out.mkdir(parents=True, exist_ok=True)
    dims = {}
    for name, (url, max_w) in IMAGES.items():
        raw = fetch(url)
        if name.endswith(".webp"):
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            if max_w and im.width > max_w:
                im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
            im.save(out / name, "WEBP", quality=80, method=6)
            dims[name] = [im.width, im.height]
        elif name.endswith(".png") and max_w:
            im = Image.open(io.BytesIO(raw)).convert("RGBA")
            if im.width > max_w:
                im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
            im.save(out / name, "PNG", optimize=True)
            dims[name] = [im.width, im.height]
        else:
            (out / name).write_bytes(raw)
            if not name.endswith(".ico"):
                with Image.open(io.BytesIO(raw)) as im:
                    dims[name] = [im.width, im.height]
    (ROOT / "data" / "images.json").write_text(json.dumps(dims, indent=1), encoding="utf-8")
    print("images", dims)


def font():
    css = fetch("https://fonts.googleapis.com/css2?family=Figtree:wght@300..900&display=swap").decode()
    blocks = re.findall(r"/\* latin \*/\s*@font-face\s*{[^}]*}", css)
    url = re.search(r"url\((https://[^)]+\.woff2)\)", blocks[0]).group(1)
    (STATIC / "fonts").mkdir(parents=True, exist_ok=True)
    (STATIC / "fonts" / "figtree-latin.woff2").write_bytes(fetch(url))
    print("font", url)


def icons():
    (STATIC / "icons").mkdir(parents=True, exist_ok=True)
    for name in ICONS:
        svg = fetch(f"https://unpkg.com/@phosphor-icons/core@2.1.1/assets/regular/{name}.svg").decode()
        (STATIC / "icons" / f"{name}.svg").write_text(svg, encoding="utf-8")
    print("icons", len(ICONS))


def leaflet():
    for f in LEAFLET_FILES:
        dest = STATIC / "vendor" / "leaflet" / f
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(fetch(f"{LEAFLET}/{f}"))
    print("leaflet", len(LEAFLET_FILES))


if __name__ == "__main__":
    images(); font(); icons(); leaflet()
