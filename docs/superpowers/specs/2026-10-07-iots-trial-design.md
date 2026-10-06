# Vela trial task: Insure On The Spot, 3-page rebuild

Date: 2026-10-07. Owner: Wrenz Ivan Laylo. Submit: tonight (PH), before the Oct 8 deadline.

## Goal
Rebuild three pages of insureonthespot.com (blog landing, locations, contact) as a working, clickable static preview that shows how Wrenz approaches an existing site: inspect what is there, decide, fix real problems, test, and verify. Keep their branding, content and visual direction. Desktop and mobile. Every button and link works.

## Deliverables (from the brief)
1. Working preview URL.
2. Desktop and mobile screenshots of each page (6 plain PNGs; optional iPhone-framed versions).
3. Short note: what was tested, 2-3 improvements and why, tools used. Plus one line on the Español finding and the contact-form question. Wrenz rewrites it in his own voice.

## Findings that drive the work (verified 2026-10-07)
- Site is WordPress (theme `orbit-media`, WP Store Locator plugin); REST API is open (594 posts, 15 categories, 4 stores).
- No meta description on any of the 3 pages.
- Blog H1 is the latest post's title; "Uncategorized" is shown to visitors; no search; 4 posts per page, "Older Articles" only.
- Locations: branch phone numbers are not tap-to-call; hours hidden behind detail pages; branch list duplicated in the HTML; no per-branch LocalBusiness schema; large blank gap; 6 of 9 images lack alt text.
- Contact: no form, addresses or map; big blank gap where a Google Reviews widget fails; hero text box overlaps text baked into the hero image at 1440px.
- Español links to a single /espanol/ page with no way back to English, `lang="en-US"` on Spanish content, no hreflang anywhere.
- Tracking (developer-call material, not the note): two GTM containers on every page; Snap pixel sends the literal placeholder `__INSERT_USER_EMAIL__`.

## Build approach
- Static HTML, one shared CSS file, small vanilla JS. No framework.
- A Python build script pulls real data from their REST API (latest 36 posts, categories) and writes the HTML. Branch data (addresses, phones, hours, notes) lives in one JSON file used by both Locations and Contact.
- Private GitHub repo `iots-trial`, one branch + PR per page, deployed to Vercel (CLI already logged in on this PC; Cloudflare's CLI is not). Each PR gets a preview link. Headers via `vercel.json`.
- URL paths match the live site: `/customer-service/blog/`, `/locations/`, `/contact/`. Root links to the three pages.

## Preview protection
`<meta name="robots" content="noindex, nofollow">` plus an `X-Robots-Tag: noindex, nofollow` header (`vercel.json`). robots.txt stays OPEN so crawlers can see the noindex (blocking crawl would hide it).

## Visual design: direction B v2 (approved mockups in `.superpowers/brainstorm/`)
- Keep: their logo, navy `#005581` / dark navy `#002d45`, yellow CTA (solid `#ffcd3c`, navy text), light grey page `#f6f8fa`, white cards.
- Type: Figtree (self-hosted, `font-display: swap`) as the free stand-in for Proxima Nova, which is Adobe-licensed to their domain. Headings 700-800 navy; body 400-500.
- Shape: cards 14px radius, buttons 10-12px, status pills fully round. One accent (yellow) for the main CTA only; status colours are semantic (green open, amber closed) and always paired with text.
- Icons: Phosphor (regular), one family. Light mode only, matching the live site.
- Real photos from their site only. No invented images, ratings or claims.
- Mobile: sticky header with yellow Call button + menu button (44px+ targets), full-width Call buttons, `viewport-fit=cover` with safe-area padding. Verified against an iPhone 15 Pro frame (393 x 852).

## Shared parts
- Header: top bar (Call now 773-202-5060, Español, Make My Payment, Renew My Policy, Customer Service, Locations, Contact Us) and main nav (Auto Insurance, SR22 Insurance, About Us, Blog, Get Free Quote). Accessible mobile menu (button, `aria-expanded`, Esc closes, focus handled).
- Español link keeps its destination but gets `lang="es"` and `hreflang="es"`.
- Footer: same columns and links as live.
- Links go to our 3 pages or to the real insureonthespot.com URL. Nothing dead.
- ZIP quote box: reuse their real quote flow if it accepts a ZIP in the URL; otherwise validate the ZIP and send to their quote page. (Checked during build.)
- Skip link, visible focus styles, `prefers-reduced-motion` respected.

## Page: Blog (`/customer-service/blog/`)
- H1 "Tips & Resources" + one-line intro.
- Topic chips at the top (horizontal scroll on mobile), "Uncategorized" hidden, each linking to the live category archive.
- Search box submitting to their WordPress search (`/?s=`).
- Newest post as a large card, then a grid of 11 text-first cards (topic, `<time>` date, title as H2 link, excerpt, descriptive link text "Read: <title>").
- Sidebar on desktop: quote box + "Need help?" customer-service links. On mobile the quote box sits after the 3rd post.
- 12 per page, static pages 1-3, then "Older articles" continues on the live blog at the matching page.
- Title "Car Insurance Tips & Resources for Chicago Drivers | Insure On The Spot", meta description, JSON-LD CollectionPage + BreadcrumbList + ItemList.

## Page: Locations (`/locations/`)
- Title band: breadcrumb, H1 "Our Locations", intro (their copy), "4 offices / Free parking at each", their existing photo.
- Desktop: branch list left, map right (sticky). Mobile: list first, map below.
- Branch card: name, note (e.g. "Next to the DMV"), live status pill, address, hours (today in bold), primary Call button (`tel:`), Directions link (Google Maps directions URL), Branch details link (live page).
- Status computed in America/Chicago time. Only published days are listed (Sunday option B): on a day with no hours the pill says when it next opens.
- Map: Leaflet + OpenStreetMap tiles, 4 pins, loaded only when scrolled near (IntersectionObserver).
- Referral callout ($100 Amazon gift card) kept. Quote box after the list.
- Title "Insure On The Spot Locations in Chicago, Berwyn & Melrose Park", meta description, alt text, JSON-LD InsuranceAgency per branch (address, geo, telephone, openingHoursSpecification, url) + BreadcrumbList.

## Page: Contact (`/contact/`)
- No hero overlap: photo without baked-in text; "Chicago's #1 Auto Insurance Agency" as real HTML text.
- H1 "Contact Us", main number large and tap-to-call.
- Customer Service and Sales hours with the same live status pill.
- "What do you need?" shortcuts to existing pages: Get a quote, Make a payment, Renew a policy, Report a claim, Roadside assistance.
- "Visit a branch": compact branch list from the same JSON.
- Reviews: plain link to their real reviews page (no ratings shown). Referral, employment link and quote box kept.
- No contact form (decision A). The note raises it as a question: who answers it and where do leads go.
- Title "Contact Insure On The Spot | Call 773-202-5060", meta description, JSON-LD ContactPage + Organization contactPoint.

## Testing (feeds "what you tested")
1. Viewports 390 / 768 / 1440 in Chromium, Firefox, WebKit (Playwright) + Wrenz on a real phone.
2. Link check: every href on the 3 pages resolves; every `tel:` matches the published number.
3. Accessibility: axe-core scan (target zero serious/critical), keyboard-only pass of menu, chips, buttons; focus and contrast.
4. Lighthouse mobile: ours vs live, recorded for the note.
5. SEO: one H1 per page, title + description present, JSON-LD parses and validates, noindex present in the live response headers.
6. Open-now logic unit tests: weekday before open, Saturday after close, Sunday, DST changeover.

## Out of scope
The Spanish page, branch detail pages, quote flow, WordPress theme work, dark mode, a contact form.

## Risks
- Their REST API or images could block hotlinking: images are downloaded into the repo at build time.
- Vercel's GitHub integration may not cover a new private repo: fall back to `vercel deploy` from the CLI for previews.
