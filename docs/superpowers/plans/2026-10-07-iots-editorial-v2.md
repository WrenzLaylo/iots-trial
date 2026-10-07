# IOTS v2 Editorial Redesign Implementation Plan

> Executed inline (Native) by the author the same afternoon. Steps use checkbox (`- [ ]`) syntax. Deadline-compact: code for the search logic lives in the task where it is written test-first; CSS/template work is described at component level and verified by screenshots plus the browser suite.

**Goal:** v2 of the three pages in the editorial direction, with instant search over all 594 posts, a designed empty state, proper pagination, and the same treatment on Locations and Contact.

**Architecture:** Same static Jinja build. New: `build/fetch_index.py` (all posts -> `data/posts_index.json`), `data/topics.json` (topic -> icon, tone), `static/js/search.js` (pure functions, unit-tested), `static/js/blog.js` (UI: state, URL, rendering, empty state, pagination), `/assets/data/posts-index.json` (compact index written by the build).

**Tech Stack:** unchanged (Python 3.11 + Jinja2, ES modules, node:test, pytest, Playwright 1.63).

**Spec:** `docs/superpowers/specs/2026-10-07-iots-editorial-v2-design.md` (on top of `2026-10-07-iots-trial-design.md`).

## Global Constraints
- Every v1 Global Constraint still holds (noindex, no canonical, brand colours, Figtree, 44px targets, no em/en dashes in our copy, no invented facts, holiday line, quote URL rules, titles <= 60, descriptions 70-160, no Claude trailers).
- Reading time = ceil(words / 230), minimum 1.
- Index loads on first interaction only; never on page load.
- Never show a bare zero-results message.

## Review Focus
1. Query with accents/punctuation ("que", "sr22", "SR-22", "Qué") must match. Test: search.test.mjs.
2. Very long or odd queries (spaces only, 100 chars, `<script>`) must not break or inject. Test: search.test.mjs highlight escapes + browser test.
3. Index slow or failing: skeleton then fallback to WordPress search. Test: qa test_index_failure_falls_back.
4. Back button after paging and filtering restores the previous view. Test: qa test_pagination_and_back.
5. No JS: default pages 1-3, chips and form still work (links + WordPress search). Test: qa no-JS test on blog.

---

### Task V1: Full post index and topic art data
- Files: `build/fetch_index.py`, `data/posts_index.json` (generated), `data/topics.json`, `build/fetch_assets.py` (more icons), `tests/test_data.py`.
- Produces: `posts_index.json` = list of `{id, title, link, date, cats:[int], words:int, excerpt_html}` newest first; `topics.json` = `{slug: {icon, tone}}` for every non-uncategorized category.
- Tests first: 594 entries (== X-WP-Total at fetch time), sorted newest first, words > 0, every category slug has an icon file and a tone in {navy, blue, pale}.

### Task V2: Search logic (test-first)
- Files: `static/js/search.js`, `tests/js/search.test.mjs`.
- Produces: `normalize(s)`, `tokens(q)`, `buildIndex(raw) -> items with .hay/.titleNorm`, `searchPosts(items, {q, topic})`, `paginate(list, page, per=12) -> {items, page, pages, from, to, total}`, `pageNumbers(current, total) -> (number|'…')[]`, `suggest(q, vocab) -> string|null`, `vocabulary(items) -> Set`, `highlight(title, q) -> safe HTML`.
- Tests: accents/punctuation; AND matching; topic filter; ranking (title before excerpt, then newest); paginate clamps out-of-range pages; pageNumbers for 1, 7, 8 and 50 pages at first/middle/last; suggest "insurence" -> "insurance", no suggestion for exact words; highlight escapes `<`, `&`, keeps original accents.

### Task V3: Build + editorial blog page
- Files: `build/build.py`, `templates/_macros.html`, `templates/_hero.html` (new), `templates/blog.html`, `static/css/site.css`, `tests/test_site.py`.
- Build writes `/assets/data/posts-index.json` (compact: topics table + post rows with title, link, date, topic index, minutes, excerpt, lang). Static pages 1-3 use the newest 36 from the index.
- Tests: hero band on blog; page 1 featured + 11 cards, pages 2-3 12 cards; every card has cover art with a topic icon and "N min read"; CTA band after the 6th card on page 1; chips are links with `data-topic`; one link per card; Spanish cards `lang="es"`; index file under 120 KB and parses.

### Task V4: Instant search UI, empty state, pagination
- Files: `static/js/blog.js`, `static/js/site.js` (load blog.js on the blog), `static/css/site.css`, `qa/test_browser.py`.
- Behaviour per spec: lazy index, instant results, URL state, aria-live count, empty state with suggestions, skeletons, failure fallback, result pagination, focus management.
- Browser tests: typing "sr22" shows results with highlighted SR-22 titles; "zzqx" shows the designed empty state (heading, tips, popular topics, WordPress search link with the query, phone link) and no bare "0"; "insurence" offers "insurance"; topic filter + query with no matches offers all-topics matches; topic with > 12 guides paginates, URL has `page=2`, Back returns to page 1; reload with `?q=sr22` restores; blocked index -> fallback message and form submits to WordPress search; axe clean on results and empty state; no layout overflow at 320px with results open.

### Task V5: Locations and Contact treatment
- Files: `templates/locations.html`, `templates/contact.html`, `templates/_hero.html`, `static/css/site.css`, `tests/test_site.py`.
- Tests: hero band on both pages with H1 inside; contact hero has the tel link; all existing v1 tests still pass.

### Task V6: QA, deploy v2, screenshots
- Rerun pytest, node, full Playwright suite, link check, Lighthouse (ours v2 vs live). Deploy and alias `iots-trial-v2.vercel.app`. Screenshots of v2 with a fixed Chicago weekday-morning clock into `deliverables/screenshots-v2/`. Commit, PR stacked on `fix/review`.
