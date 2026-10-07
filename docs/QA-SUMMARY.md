| page | perf | a11y | best practices | LCP |
|---|---|---|---|---|
| live-blog | 27 | 95 | 54 | 16.2 s |
| live-contact | 27 | 88 | 54 | 18.7 s |
| live-locations | 26 | 87 | 54 | 19.6 s |
| ours-blog | 99 | 100 | 100 | 1.6 s |
| ours-contact | 100 | 100 | 100 | 1.1 s |
| ours-locations | 100 | 100 | 100 | 1.1 s |

Lighthouse: mobile, run 2026-10-07 against https://iots-trial.vercel.app (ours) and https://www.insureonthespot.com (live). SEO category skipped on purpose (our preview is noindexed by design). Part of the live site's gap is its marketing tags (2 GTM containers, Facebook, TikTok, Snap, StackAdapt, PostHog, OptinMonster), which production would still need.

Browser QA (qa/test_browser.py, 26 checks, all passing):
- No horizontal overflow and no script errors: Chromium, Firefox, WebKit at 320 / 390 / 768 / 1440 px, all 3 pages.
- axe-core: 0 violations at any impact level, 390 and 1440 px.
- Layout shift on a phone with a slow script: blog 0, locations 0.033, contact 0.038 (was 0.612 before the menu fix).
- Keyboard: skip link is the first stop, every stop has a visible focus ring, focus reaches the footer (no trap in the map).
- Status pills use Chicago time from a Manila clock; JS-off page keeps hours, phone links, menu and a working quote form; ZIP validation; map loads 4 pins and degrades to the Google Maps link if Leaflet/tiles are blocked.

Links (qa/check_links.py): 88 checked, all 2xx/3xx except bbb.org (403 to scripts: Cloudflare "Just a moment" bot check; same profile URL their live BBB seal uses, opens normally for a person).

Structured data (validator.schema.org, deployed pages): locations 5 objects, contact 2, blog 3; 0 errors, 0 warnings.

## v2 (editorial), 2026-10-07
Lighthouse mobile (https://iots-trial.vercel.app): blog 97 / 100 / 100 (perf / a11y / best practices), locations 100 / 100 / 100, contact 100 / 100 / 100. LCP 1.6-1.7 s, CLS 0 to 0.037.
Browser QA (qa/test_browser.py, 42 checks, all passing): v1 checks plus instant search (results, accents, empty state, did-you-mean, topic fallback, pagination + Back, reload restores, index failure falls back to WordPress search, typing before the script loads, axe on results and empty state at 390px).
Unit tests: pytest 56, node 22 (search: normalize, matching, ranking, pagination, page numbers, did-you-mean, safe highlighting).
Structured data (validator.schema.org, deployed): blog 3 objects, locations 5, contact 2; 0 errors, 0 warnings.
Links: 88 checked; all fine except bbb.org (bot check) and one 429 rate-limit during the bulk run that returns 200 on retry.
