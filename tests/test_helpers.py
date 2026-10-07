import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build"))
from build import clean_excerpt, directions_url, fmt_time, group_hours, paginate  # noqa: E402

HQ = {d: ["08:00", "20:00"] for d in ["mon", "tue", "wed", "thu", "fri"]} | {"sat": ["08:00", "17:30"]}


def test_fmt_time():
    assert fmt_time("08:00") == "8:00 AM"
    assert fmt_time("20:30") == "8:30 PM"
    assert fmt_time("12:00") == "12:00 PM"


def test_group_hours_weekdays_and_saturday():
    assert group_hours(HQ) == [
        {"label": "Mon-Fri", "days": "mon tue wed thu fri", "text": "8:00 AM to 8:00 PM"},
        {"label": "Sat", "days": "sat", "text": "8:00 AM to 5:30 PM"},
    ]


def test_group_hours_gap_breaks_the_run():
    h = {"mon": ["09:00", "17:00"], "tue": ["09:00", "17:00"], "thu": ["09:00", "17:00"]}
    assert [r["label"] for r in group_hours(h)] == ["Mon-Tue", "Thu"]


def test_clean_excerpt_strips_read_more_and_entities():
    raw = ('<p class="wp-block-paragraph">Driving in Chicago can be challenging, especially when the weather '
           'gets foggy &amp; cold&hellip;&nbsp;<a class="more" href="https://x">Read More &rsaquo;</a></p>')
    assert clean_excerpt(raw) == "Driving in Chicago can be challenging, especially when the weather gets foggy & cold…"


def test_clean_excerpt_cuts_on_a_word():
    raw = "<p>" + "word " * 60 + "</p>"
    out = clean_excerpt(raw, limit=40)
    assert out.endswith("…") and len(out) <= 41 and not out[:-1].endswith(" ")


def test_directions_url():
    b = {"street": "5485 N Elston Ave", "city": "Chicago", "state": "IL", "zip": "60630"}
    assert directions_url(b) == "https://www.google.com/maps/dir/?api=1&destination=5485+N+Elston+Ave%2C+Chicago%2C+IL+60630"


def test_paginate():
    pages = paginate(list(range(36)), 12, 3)
    assert [len(p) for p in pages] == [12, 12, 12] and pages[1][0] == 12
