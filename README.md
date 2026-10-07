# Insure On The Spot: blog, locations and contact rebuild

A trial task for Vela: rebuild and improve three pages of insureonthespot.com while keeping their brand, content and URLs.

**Live preview:** https://iots-trial.vercel.app (noindexed on purpose)

| Page | Preview | Live site |
|---|---|---|
| Tips & Resources (blog) | [/customer-service/blog/](https://iots-trial.vercel.app/customer-service/blog/) | [live](https://www.insureonthespot.com/customer-service/blog/) |
| Our Locations | [/locations/](https://iots-trial.vercel.app/locations/) | [live](https://www.insureonthespot.com/locations/) |
| Contact Us | [/contact/](https://iots-trial.vercel.app/contact/) | [live](https://www.insureonthespot.com/contact/) |

## What changed and why

I audited the live pages before building and logged 26 issues: [docs/FINDINGS.md](docs/FINDINGS.md). The main fixes:

- **Blog:** instant search across all 594 posts (handles typos and accents, with a helpful no-results state), topic filters, numbered pages, topic cover art and reading times. The H1 is now the page title instead of the latest post's title.
- **Locations:** every branch can be called with one tap, shows its hours, and has a live open/closed label in Chicago time. Before, hours were only on each branch's own detail page. There's also a map that loads only when you scroll to it.
- **Contact:** Call and Get Free Quote buttons at the top, phone hours, shortcuts (payments, claims, roadside) and all four branches.
- **SEO basics:** meta descriptions, one H1 per page, heading order, alt text, structured data for each branch, and `lang="es"` on the Español link and the 45 Spanish posts.

Results: [docs/QA-SUMMARY.md](docs/QA-SUMMARY.md). Lighthouse mobile performance went from 26-27 on the live pages to 97-100, with accessibility at 100.

## How it's built

- `build/fetch_*.py` pulls the posts, categories and images from their public WordPress REST API into `data/`. Branch addresses, phones and hours in `data/branches.json` come from their store locator and branch pages. Nothing is made up.
- `build/build.py` renders `templates/` (Jinja2) into static HTML in `site/`, which Vercel serves.
- `static/js/` holds small browser modules with no framework: search, blog UI, open/closed hours, ZIP quote box, mobile menu, map.

```bash
pip install -r requirements-dev.txt
python build/build.py                    # writes site/
python -m http.server -d site 8000       # preview at http://localhost:8000
```

## Tests

```bash
python -m pytest                         # page and data checks
npm install && npm run test:js           # search, hours and quote logic (node:test)
python -m playwright install
python -m pytest qa/test_browser.py      # Chromium, Firefox, WebKit: axe, keyboard, no-JS, layout shift
```

## History

The work is split into pull requests, one per step (foundation, blog, locations, contact, QA, review fixes, the editorial redesign, v3, contact buttons). An earlier, closer-to-the-original version is tagged `v1-classic` and live at https://iots-trial-classic.vercel.app
