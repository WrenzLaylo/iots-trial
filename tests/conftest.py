import json
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build"))


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.html, self.tags, self.jsonld, self._capture, self.title, self.texts = html, [], [], None, "", {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "title" or (tag == "script" and a.get("type") == "application/ld+json") or tag in ("h1",):
            self._capture = [tag, ""]

    def handle_data(self, data):
        if self._capture:
            self._capture[1] += data

    def handle_endtag(self, tag):
        if self._capture and tag == self._capture[0]:
            if tag == "title":
                self.title = self._capture[1].strip()
            elif tag == "script":
                self.jsonld.append(json.loads(self._capture[1]))
            else:
                self.texts.setdefault(tag, []).append(self._capture[1].strip())
            self._capture = None

    def find(self, tag, **attrs):
        return [a for t, a in self.tags if t == tag and all(a.get(k.replace("_", "-")) == v for k, v in attrs.items())]


@pytest.fixture(scope="session")
def site(tmp_path_factory):
    from build import render_all
    out = tmp_path_factory.mktemp("site")
    render_all(out)
    return out


def parse(site: Path, rel: str) -> Page:
    path = site / rel.strip("/") / "index.html" if rel.strip("/") else site / "index.html"
    return Page(path.read_text(encoding="utf-8"))
