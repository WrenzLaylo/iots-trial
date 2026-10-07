# Insure On The Spot: audit findings (blog, locations, contact)

Audited 2026-10-07 by Wrenz Ivan Laylo. Every item below was checked on the live site (HTML, HTTP headers, REST API or a headless browser), not assumed.

Status key:
- **Fixed** = fixed in the preview build.
- **Improved** = partly addressed in the preview; the rest needs their side.
- **Recommend** = outside the 3 pages or needs their decision; recommendation given.
- **Dev call** = worth raising on the developer call, not in the short note.

Severity: **H** hurts calls/quotes or search visibility now, **M** noticeable quality or accessibility problem, **L** minor or housekeeping.

## Summary

| # | Area | Finding | Sev | Status |
|---|------|---------|-----|--------|
| 1 | Conversion | Branch phone numbers on Locations are not tap-to-call | H | Fixed |
| 2 | Conversion | Branch hours hidden behind 4 separate detail pages | H | Fixed |
| 3 | SEO | No meta description on any of the 3 pages | H | Fixed |
| 4 | SEO | Blog H1 is the latest post's title | M | Fixed |
| 5 | Layout | Large blank gaps on Locations and Contact | M | Fixed |
| 6 | Layout | Contact hero: quote box overlaps text baked into the image | M | Fixed |
| 7 | Conversion | Contact page has no addresses, map, form or email | M | Improved |
| 8 | Conversion | Quote button uses http, redirect duplicates the ZIP, bad ZIP dropped silently | M | Fixed (ours) / Recommend |
| 9 | SEO | No per-branch local business structured data | M | Fixed |
| 10 | SEO/a11y | Heading levels skip (H1 to H3) on Locations and Contact | M | Fixed |
| 11 | SEO | Branch list duplicated in the Locations HTML | L | Fixed |
| 12 | a11y/SEO | Images missing alt text | M | Fixed |
| 13 | a11y | "›" arrow is part of every blog post heading | L | Fixed |
| 14 | UX | Blog: no search box; topics buried at the bottom on phones | M | Fixed |
| 15 | SEO | Blog pagination: 4 per page, 149 pages, no page numbers | M | Improved |
| 16 | Content | "Uncategorized" topic (51 posts) shown to visitors | L | Improved / Recommend |
| 17 | Content | No new blog post since 2026-07-05 | M | Dev call |
| 18 | Content | Branch detail pages quote July 2015 census numbers | L | Recommend |
| 19 | i18n/SEO | Español: one page for every link, no way back, wrong lang, no hreflang | H | Improved / Recommend |
| 20 | Mobile | Phones: branches start far down the page; no map on mobile | M | Fixed |
| 21 | Security | Quote subdomain's HSTS header arrives with a corrupted name | L | Dev call |
| 22 | Tracking | Two Google Tag Manager containers on every page | M | Dev call |
| 23 | Tracking | Snapchat pixel sends a literal placeholder instead of an email | L | Dev call |
| 24 | Performance | 22-24 external scripts and 12-16 stylesheets per page | M | Improved |
| 25 | Performance | BBB seal loaded through extra third-party script / iframe | L | Fixed |
| 26 | Info | Brand font is Adobe Typekit, licensed to their domain | - | Noted |

## Details

### 1. Branch phone numbers are not tap-to-call (H, Fixed)
- **Evidence:** on /locations/ the only `tel:` links are the main 773-202-5060 (2 links). The four branch numbers ((773) 202-5060, (773) 202-0651, (708) 857-7661, (708) 547-1800) are plain text.
- **Impact:** on a phone, a visitor who wants a specific branch has to copy the number by hand. Calls are their main conversion.
- **Preview:** every branch has a Call button with the correct `tel:` link.

### 2. Branch hours hidden (H, Fixed)
- **Evidence:** /locations/ shows "See Hours & Details" only. Hours differ a lot by branch (from the four detail pages):
  - HQ: Mon-Fri 8:00-8:00, Sat 8:00-5:30
  - Chicago South: Mon-Fri 9:30-6:00, Sat 9:00-3:00
  - Berwyn: Mon-Fri 9:30-6:00, Sat 9:00-3:00
  - Melrose Park: Mon-Fri 8:00-6:00, Sat 8:00-2:00
- **Impact:** four extra page loads to answer "is my branch open?". Someone assuming HQ hours could arrive at Chicago South after it closes.
- **Preview:** hours on every card, today in bold, live open/closed status in Chicago time, and "Holiday hours may vary, call to confirm."

### 3. No meta descriptions (H, Fixed)
- **Evidence:** no `<meta name="description">` on /customer-service/blog/, /locations/ or /contact/.
- **Impact:** Google writes its own snippet from page text, often the nav or the gift-card promo.
- **Preview:** written for each page from their own content.

### 4. Blog H1 is a post title (M, Fixed)
- **Evidence:** the H1 on /customer-service/blog/ is "How to Defog Windshield & Windows in Chicago", which is also the first post's H2.
- **Impact:** the page's main heading describes one post instead of the blog, and repeats a heading that belongs to another URL.
- **Preview:** H1 "Tips & Resources" + intro.

### 5. Large blank gaps (M, Fixed)
- **Evidence:** full-page screenshots at 1440px and 390px: a few hundred pixels of empty space between the intro and the map on /locations/, and a large empty block around the Google Reviews image on /contact/ (a reviews widget that does not render).
- **Impact:** looks broken; pushes content down.

### 6. Contact hero overlap (M, Fixed)
- **Evidence:** at 1440px the "Free Auto Insurance Quote in 2 Minutes!" box covers part of "Chicago's #1 Auto Insurance Agency", which is text baked into the hero image (`iots-hero.webp`; `new-hero.png` has the same baked text).
- **Impact:** looks broken, and baked-in text cannot be read by search engines or screen readers and does not reflow on phones.
- **Preview:** their staff photo without text (`JP2_1071_web.jpg`); the claim is real HTML text.

### 7. Contact page is thin (M, Improved)
- **Evidence:** /contact/ has one phone number, two sets of hours and a Location Finder link. No addresses, no map, no form, no email.
- **Preview:** the four branches (call, directions, live status) and shortcuts to payments, renewals, claims, roadside and FAQs.
- **Recommend / question for them:** a contact or callback form needs a decision on who answers it and where leads go (email, CRM). Not added without that.

### 8. Quote button (M, Fixed in ours / Recommend)
- **Evidence:** the footer button runs `redirect_to_quote()`, which sends visitors to `http://quote.insureonthespot.com/?zipcode=NNNNN`. That URL returns a 301 to `https://quote.insureonthespot.com/?zipcode=60630&zipcode=60630` (parameter duplicated). An invalid ZIP silently goes to the quote page with no message. The https URL keeps the ZIP prefilled.
- **Impact:** an extra redirect hop, a first request that is not encrypted (newer Chrome and Safari upgrade it automatically, older browsers do not), and a sloppy redirect rule.
- **Preview:** links straight to the https URL with one parameter; a ZIP that is not 5 digits shows an inline error.
- **Recommend:** change `http` to `https` in the theme's footer script and fix the redirect rule.

### 9. No local business structured data (M, Fixed)
- **Evidence:** the only JSON-LD on these pages is WebPage / BreadcrumbList / WebSite / Organization. No branch is described as a local business.
- **Preview:** an InsuranceAgency entry per branch (address, coordinates, phone, opening hours, URL), ContactPage + contact point on Contact, CollectionPage + ItemList on the blog.

### 10. Heading levels skip (M, Fixed)
- **Evidence:** /locations/ and /contact/ each have one H1, no H2 and one H3 ("Free Auto Insurance Quote in 2 Minutes!").
- **Impact:** a broken outline for screen readers and a weaker structure for search.

### 11. Branch list duplicated (L, Fixed)
- **Evidence:** the four branches appear twice in the /locations/ HTML (two copies of the store-locator list).
- **Impact:** repeated content and confusing for screen readers.

### 12. Missing alt text (M, Fixed)
- **Evidence:** images without useful alt text: 6 of 9 on /locations/, 4 of 8 on /contact/, 1 of 3 on the blog.

### 13. Arrow inside blog headings (L, Fixed)
- **Evidence:** each post title is `<h2 class="postTitle"><a ...>Title&nbsp;&rsaquo;</a></h2>`.
- **Impact:** screen readers read the arrow as part of the title, and it ends up in the heading outline.
- **Preview:** decorative arrow added with CSS, not in the text.

### 14. Blog search and topics (M, Fixed)
- **Evidence:** no search box on the blog. On a 390px phone the "Choose a topic" list sits below all posts and the quote box.
- **Preview v1:** topic chips at the top, and a search box that uses their own WordPress search (`/?s=`, verified working).
- **Preview v2:** results appear as you type across all 594 guides (accent- and typo-tolerant, with a designed empty state); topic chips filter in place; their WordPress search stays as the fallback without JavaScript or if the index fails.

### 15. Blog pagination (M, Improved)
- **Evidence:** 4 posts per page, 594 posts = 149 pages, navigation is only "Older Articles" (`/customer-service/blog/page/2/`).
- **Impact:** older posts are many clicks deep for visitors and crawlers.
- **Preview:** 12 per page with numbered pages 1-3, then a link to the matching live page (page 10 starts at post 37).
- **Recommend:** raise posts per page and add numbered pagination on the live blog.

### 16. "Uncategorized" (L, Improved / Recommend)
- **Evidence:** the topic list shows "Uncategorized" (51 posts, from the REST API).
- **Preview:** hidden from visitors.
- **Recommend:** re-file those 51 posts into real topics.

### 17. Blog has stopped publishing (M, Dev call)
- **Evidence:** newest post in the REST API is dated 2026-07-05; posts before that were daily (July 1-5).
- **Worth asking:** paused on purpose, or did a scheduled-content pipeline stop?

### 18. Outdated branch page copy (L, Recommend)
- **Evidence:** the Berwyn and Melrose Park pages cite "United States Census Bureau estimate(s) of July 2015".

### 19. Español (H, Improved / Recommend)
- **Evidence:** the "Español" link on every page goes to the single page /espanol/. That page has no link back to English (its top bar still says "Español"), declares `<html lang="en-US">` on Spanish content, and no page has hreflang tags.
- **Impact:** Spanish speakers lose the page they were on and get stuck; screen readers use English pronunciation; search engines get no language pairing.
- **Also:** 45 of the 594 posts are in Spanish, mixed into the English blog with no language marking and no Spanish section (e.g. "Seguro de Auto con Pago Inicial Bajo en Chicago..."). The preview marks those cards `lang="es"`.
- **Preview:** the link is kept and marked `lang="es"` and `hreflang="es"`. No `<link rel="alternate" hreflang>`, because these 3 pages have no Spanish equivalents.
- **Recommend:** a language switcher on both versions, `lang="es"` on Spanish pages, hreflang pairs wherever a translation exists.

### 20. Mobile layout (M, Fixed)
- **Evidence:** at 390px the Locations hero and intro push the first branch about 1,600px down; the map does not appear on phones.
- **Preview:** branches right after a compact title; map below the list; sticky header with a Call button.

### 21. Corrupted HSTS header on the quote subdomain (L, Dev call)
- **Evidence:** `https://quote.insureonthespot.com/` returns the header twice with broken names: `!!!!Strict-Transport-Security` and `22Strict-Transport-Security`. Browsers ignore unknown header names, so HSTS is not applied from that host. www.insureonthespot.com sends a correct header.
- **Worth asking:** probably a proxy or server config issue on the quote host.

### 22. Two GTM containers (M, Dev call)
- **Evidence:** GTM-5NQZ26X and GTM-5XW2TR3 load on all three pages.
- **Impact (unverified):** if both fire the same tags, pageviews and conversions are counted twice. Needs access to their GTM to confirm.

### 23. Snapchat pixel placeholder (L, Dev call)
- **Evidence:** `snaptr('init', ..., {'user_email': '__INSERT_USER_EMAIL__'})` on every page: a template placeholder that was never replaced.

### 24. Script weight (M, Improved)
- **Evidence:** 22-24 external scripts and 12-16 stylesheets per page. Marketing and analytics on all three pages: 2 GTM containers, PostHog, Facebook pixel, TikTok, Snapchat, StackAdapt, plus OptinMonster.
- **Preview:** a handful of first-party files.
- **Honest caveat:** the preview has none of their marketing tags, which production still needs. Part of any Lighthouse gap comes from that.

### 25. BBB seal (L, Fixed)
- **Evidence:** /contact/ loads `seal-chicago.bbb.org/inc/legacy.js`; /locations/ embeds the seal as an iframe.
- **Preview:** the same trust signal as a static linked badge (their image, links to their BBB profile), no third-party script.

### 26. Brand font (info)
- **Evidence:** headings and body use `proxima-nova` from Adobe Typekit (`use.typekit.net/nnl3woo.css`), licensed to their domain.
- **Preview:** Figtree (free, open licence) as the closest match. Production would keep their Typekit font.

## Site facts used in the build
- Platform: WordPress, theme `orbit-media`; plugins seen: WP Store Locator, Ninja Forms, Link Whisper, OptinMonster, Superfly Menu, FacetWP.
- REST API open: 594 posts, 15 categories, 4 stores.
- Quote tool: `https://quote.insureonthespot.com/?zipcode=NNNNN` (ZIP prefilled).
- Customer portal (payments and renewals): `https://csp.insureonthespot.com/Login.aspx`.
- Contact hours: Customer Service Mon-Fri 8am-8pm, Sat 8am-5pm; Sales Mon-Fri 8am-8:30pm, Sat 8am-5:30pm.
