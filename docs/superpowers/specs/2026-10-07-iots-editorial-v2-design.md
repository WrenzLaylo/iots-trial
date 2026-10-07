# IOTS trial, v2 "editorial" redesign (addendum)

Date: 2026-10-07. Builds on `2026-10-07-iots-trial-design.md`; everything there still applies unless replaced here. v1 is preserved as git tag `v1-classic`. Wrenz compares v1 and v2 and picks the winner for submission.

## Why
Wrenz's review of v1: generic, not premium; search should show results immediately; blog cards don't invite reading and are tiring. Their posts have no images (0 of the 36 newest) and average ~2,300 words, so the cards need a visual system that is not stock photography. Direction chosen: A, editorial.

## Blog
- Navy hero band: breadcrumb, H1 "Tips & Resources", lede, large search field ("Search 594 guides", `/` shortcut), topic chips (real links to the live category archives, enhanced to filter in place).
- Page 1: featured latest guide (large card with cover art). Pages 2-3: no featured card.
- 3-column grid (2 at tablet, 1 on phones). Card = topic cover art (topic icon + tone, watermark icon), topic, reading time ("11 min read" = ceil(words/230)), title, 2-line excerpt, date. One link per card.
- Cover art: one Phosphor icon per topic, three brand tones (navy, blue, pale). Posts with no topic use a newspaper icon. No invented photos.
- Quote CTA band after the 6th card (their copy: lowest rates, we shop you save, SR22s filed electronically). "Need help?" strip at the bottom (payments, roadside, claims, FAQs).
- Default view stays server-rendered pages 1-3 (crawlable, works without JS); page 3 continues to the live blog page 10.
- Spanish posts keep `lang="es"`.

## Instant search and topic filtering (JS)
- Index of all 594 posts built from their REST API, served as `/assets/data/posts-index.json`, loaded on first interaction (focus, typing, chip click), not on page load.
- Matching: accent-insensitive, punctuation-insensitive ("sr22" = "SR-22"), every word must match (title, topic, excerpt). Rank: words in the title first, then newest. Matches highlighted in titles.
- Results update as you type. URL state `?q=&topic=&page=` (typing replaces history; topic and page changes push), so Back, refresh and sharing work. Esc / clear button resets. Result count announced via `aria-live`.
- Results header: "23 guides for "sr22"", "96 guides in Coverages", or both.
- Pagination in results: 12 per page; numbered pages with collapsing ellipsis (1 2 3 ... 8), Previous/Next, "Showing 13-24 of 96"; page change scrolls to and focuses the results heading.
- Empty state (never a bare "0 results"): heading "No guides match "xyz" yet"; if a topic filter hides matches, offer them ("4 guides match in all topics"); "Did you mean ...?" from words in their titles (edit distance); tips (fewer or different words); popular topic chips; "Search the whole website" (their WordPress search with the query); "Prefer to ask? Call 773-202-5060".
- Loading: skeleton cards while the index loads. Error: if the index fails, show a short message and let the form submit to their WordPress search.

## Locations and Contact
- Same navy hero band. Locations: breadcrumb, H1, lede, "4 offices / free parking at each", photo in a rounded frame. Contact: eyebrow, H1, lede, big phone number (yellow), photo.
- Cards: borderless, soft tinted shadow, 16px radius; clickable cards lift slightly on hover. Larger section headings. Content, status pills, hours, holiday line, map unchanged.

## Testing additions
- node:test: normalize, tokenize, match, rank, paginate, page-number collapsing, did-you-mean, highlight.
- pytest: index file shape and size; hero on all pages; cover art per card; reading time; CTA after the 6th card on page 1; chips are links with data-topic.
- Playwright: instant results; "sr22" and "que" matching; empty state content (no bare zero); did-you-mean; topic-hidden matches; pagination and URL/Back; index failure fallback; axe on results and empty state; all v1 checks rerun.

## Delivery
Branch `feat/editorial` (PR stacked on `fix/review`), preview alias `iots-trial-v2.vercel.app` (Vercel login). Winner becomes `iots-trial.vercel.app`; retake screenshots with a fixed Chicago daytime clock; update the note.
