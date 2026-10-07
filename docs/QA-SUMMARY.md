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
