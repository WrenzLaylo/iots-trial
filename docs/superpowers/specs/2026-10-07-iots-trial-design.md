# Vela trial task: Insure On The Spot, 3-page rebuild

Date: 2026-10-07 (rev 2 after review). Owner: Wrenz Ivan Laylo. Submit: tonight (PH), before the Oct 8 deadline.

## Goal
Rebuild three pages of insureonthespot.com (blog landing, locations, contact) as a working, clickable static preview that shows how Wrenz approaches an existing site: inspect what is there, decide, fix real problems, test, and verify. Keep their branding, content and visual direction. Desktop and mobile. Every button and link works.

## Deliverables (from the brief)
1. Working preview URL that opens for anyone, logged out.
2. Desktop and mobile screenshots of each page (6 plain full-page PNGs; iPhone-framed versions optional).
3. Short note (aim for under 200 words): what was tested, 2-3 improvements and why, tools used. Plus one line on the Español finding and the contact-form question. Wrenz rewrites it in his own voice.

## Findings that drive the work (all verified on the live site 2026-10-07)
- WordPress (theme `orbit-media`, WP Store Locator, Ninja Forms); REST API open (594 posts, 15 categories, 4 stores).
- No meta description on any of the 3 pages.
- Blog: H1 is the latest post's title; "Uncategorized" (51 posts) shown to visitors; no search box; 4 posts per page with only "Older Articles"; no new post since 2026-07-05 (3 months).
- Locations: branch phones not tap-to-call; hours hidden behind detail pages; branch list duplicated in the HTML; no per-branch LocalBusiness schema; large blank gap; 6 of 9 images lack alt text.
- Contact: no form, no addresses, no map; big blank gap where a Google Reviews widget fails; hero quote box overlaps "Chicago's #1" text that is baked into the hero image at 1440px.
- Quote box: `redirect_to_quote()` sends to `http://quote.insureonthespot.com/?zipcode=NNNNN` (plain http); that 301s to https but duplicates the parameter (`?zipcode=60630&zipcode=60630`); an invalid ZIP is silently dropped with no message.
- Español: one /espanol/ page for every link, no way back to English, `lang="en-US"` on Spanish content, no hreflang anywhere.
- Tracking (developer-call material, not the note): two GTM containers on every page; Snap pixel sends the literal placeholder `__INSERT_USER_EMAIL__`; BBB seal loaded through an extra `legacy.js` script.

## Build approach
- Static HTML, one shared CSS file, small vanilla JS. No framework.
- Python build script pulls real data from their REST API (latest 36 posts, categories) and writes the HTML. Excerpts are cleaned (HTML tags, "[...]", "Read More" removed).
- `data/branches.json` holds addresses, phones, hours, notes and coordinates for the 4 branches (coordinates geocoded once with OpenStreetMap Nominatim, then stored). Locations and Contact both read it, so they can never disagree.
- Their images are downloaded into the repo (no hotlinking), converted to WebP, with width/height set (no layout shift) and real alt text.
- Private GitHub repo `iots-trial`, one branch + PR per page, deployed to Vercel (CLI logged in here; Cloudflare's is not). Headers via `vercel.json`.
- URL paths match the live site: `/customer-service/blog/`, `/locations/`, `/contact/`. Root links to the three pages.

## Preview protection and canonicals
- `<meta name="robots" content="noindex, nofollow">` plus `X-Robots-Tag: noindex, nofollow` (`vercel.json`). robots.txt stays OPEN so crawlers can see the noindex (blocking crawl would hide it).
- No `rel=canonical` on the preview: a canonical pointing at production next to a noindex sends Google mixed signals. Production keeps its existing self-canonicals.
- JSON-LD uses the production URLs, so it is ready to copy into the real site.
- Vercel protects preview deployments of private repos with a login wall by default. The URL we submit is the project's production deployment with Deployment Protection off, checked in a logged-out browser before sending.

## Visual design: direction B v2 (approved mockups in `.superpowers/brainstorm/`)
- Keep: their logo, navy `#005581` / dark navy `#002d45`, yellow CTA (solid `#ffcd3c`, navy text), light grey page `#f6f8fa`, white cards.
- Type: Figtree, self-hosted (OFL licence, `font-display: swap`), as the free stand-in for Proxima Nova, which is Adobe-licensed to their domain. Production would keep their Typekit font. Headings 700-800 navy; body 400-500, 16px minimum.
- Shape: cards 14px radius, buttons 10-12px, status pills fully round. Yellow is used only for the main CTA; status colours are semantic (green open, amber closed) and always paired with text.
- Icons: Phosphor (regular), one family. Light mode only, matching the live site.
- Real photos from their site only. No invented images, ratings or claims.
- Mobile: sticky header with yellow Call button + menu button (44px+ targets), full-width Call buttons, `viewport-fit=cover` with safe-area padding. Checked against an iPhone 15 Pro frame (393 x 852).

## Shared parts
- Header: top bar (Call now 773-202-5060, Español, Make My Payment, Renew My Policy, Customer Service, Locations, Contact Us) and main nav (Auto Insurance, SR22 Insurance, About Us, Blog, Get Free Quote). Accessible mobile menu (button, `aria-expanded`, Esc closes, focus returns to the button).
- Español link keeps its destination and gets `lang="es"` and `hreflang="es"` on the link. No `<link rel="alternate" hreflang>` tags: there are no Spanish versions of these 3 pages to pair with.
- Quote box keeps their selling points (Lowest rates in Chicagoland, We shop, you save, SR22s filed electronically). It sends to `https://quote.insureonthespot.com/?zipcode=NNNNN` (https directly, one parameter). A ZIP that is not 5 digits shows an inline error under the field; an empty field goes to the quote page without a ZIP, same as today.
- Trust signals kept: BBB accreditation as a static linked badge (their image, links to their BBB profile, no extra script), "See what our customers are saying" reviews link, "Trusted since 1986".
- Footer: same columns and links as live. All links go to our 3 pages or to verified live URLs. Nothing dead.
- Skip link, visible focus styles, `prefers-reduced-motion` respected.

## Page: Blog (`/customer-service/blog/`)
- H1 "Tips & Resources" + one-line intro.
- Topic chips at the top (horizontal scroll on mobile, keyboard reachable), "Uncategorized" hidden, each linking to the live category archive.
- Search box submitting to their WordPress search (`/?s=`, verified working).
- Newest post as a large card, then a grid of 11 text-first cards (topic, `<time>` date, title, excerpt). One link per card: the title link covers the whole card, so screen readers don't hear each post twice.
- Sidebar on desktop: quote box + "Need help?" links (Payment options, Roadside assistance, Report a claim, Auto insurance FAQs). On mobile the quote box sits after the 3rd post.
- 12 per page, static pages 1-3 at `/customer-service/blog/page/2/` and `/page/3/` (same pattern as live). After page 3, "Older articles" links to the live `/customer-service/blog/page/10/`, which starts at post 37 (their 4-per-page layout; verified).
- Title "Car Insurance Tips for Chicago Drivers | Insure On The Spot" (under 60 characters), meta description, JSON-LD CollectionPage + BreadcrumbList + ItemList.

## Page: Locations (`/locations/`)
- Title band: breadcrumb, H1 "Our Locations", intro (their copy), "4 offices / Free parking at each" (all four branch pages say free parking), their existing photo.
- Desktop: branch list left, map right (sticky). Mobile: list first, map below.
- Branch card: name, note (HQ and Melrose Park: "Next to the DMV"), live status pill, address, hours (today in bold), primary Call button (`tel:`), Directions link (`https://www.google.com/maps/dir/?api=1&destination=<address>`, opens the maps app on phones), Branch details link (live page).
- Status pill is computed in the browser at view time in America/Chicago time and refreshed every minute. The HTML itself shows the hours, so the page works without JavaScript. Only published days are listed (Sunday option B): on a day with no hours the pill says when it next opens. Holidays are unknown to the site, so the pill can be wrong on a holiday (open question below).
- Map: Leaflet + OpenStreetMap tiles with the required attribution, 4 pins, loaded only when scrolled near (IntersectionObserver). If it fails or JS is off, a "View on Google Maps" link shows instead.
- Referral callout ($100 Amazon gift card) and BBB badge kept. Quote box after the list.
- Title "Locations: Chicago, Berwyn & Melrose Park | Insure On The Spot", meta description, JSON-LD InsuranceAgency per branch (address, geo, telephone, openingHoursSpecification, url, parentOrganization) + BreadcrumbList.

## Page: Contact (`/contact/`)
- Hero photo without baked-in text: their staff photo with the toy car (`JP2_1071_web.jpg`, already used on this page). "Chicago's #1 Auto Insurance Agency" becomes real HTML text.
- H1 "Contact Us", main number large and tap-to-call.
- Customer Service and Sales hours (their published hours) with the same live status pill.
- "What do you need?" shortcuts to verified live pages: Get a quote, Make a payment / Renew (customer portal), Report a claim, Roadside assistance, Auto insurance FAQs.
- "Visit a branch": compact branch list from `branches.json`.
- Reviews link, BBB badge, referral, employment link and quote box kept. No star ratings shown.
- No contact form (decision A). The note raises it as a question: who would answer it and where should leads go.
- Title "Contact Insure On The Spot | Call 773-202-5060", meta description, JSON-LD ContactPage + Organization contactPoint.

## Testing (feeds "what you tested")
1. Viewports 390 / 768 / 1440 in Chromium, Firefox, WebKit (Playwright) + Wrenz on his real phone.
2. Link check: every href on the 3 pages resolves (polite, rate-limited); every `tel:` matches the published number; quote box sends the right URL for a valid ZIP and shows the error for an invalid one.
3. Accessibility: axe-core scan (target zero serious/critical), keyboard-only pass of menu, chips, buttons and map; focus and contrast.
4. Lighthouse mobile, ours vs live. The note says plainly that part of the gap is because the preview carries none of their marketing tags (2 GTM containers, Facebook, TikTok, Snap, StackAdapt, PostHog), which production would still need.
5. SEO: one H1 per page, title + description present, JSON-LD parses and validates, noindex present in the deployed response headers.
6. Open-now logic unit tests: weekday before open, during, after close, Saturday after close, Sunday, DST changeover (Nov 1, 2026).
7. Final check of the submitted URL in a logged-out browser window.

## Priorities (if time runs short, cut from the bottom)
- Must: shared header/footer, the 3 pages with every fix above, schema, noindex, link + a11y + viewport tests, deploy, screenshots, note.
- Should: live status pills, blog pages 2-3, Lighthouse comparison.
- Could: Leaflet map (fallback: "View on Google Maps" link per branch), iPhone-framed screenshots.

## Out of scope
The Spanish page, branch detail pages, the quote flow itself, WordPress theme work, dark mode, a contact form, analytics tags.

## Open question for Wrenz
- Holiday hours: add a small "Holiday hours may vary, call to confirm" line under branch hours? It is new copy (not on their site), but it prevents the status pill from saying "Open" on a holiday. Default if no answer: add it.

## Risks
- Vercel's GitHub integration may not have access to a new private repo: deploy with the `vercel` CLI instead.
- Their REST API or images could start blocking: data and images are saved into the repo at build time, so the preview does not depend on their server.
- Using their logo and photos on a public URL: noindexed, temporary, for their review only; take it down after the hiring decision.
