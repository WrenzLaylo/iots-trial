# Vela submission form: draft answers (rewrite in your own words before sending)

## Video walkthrough (Loom or similar)
Option A (recommended): record a short Loom with your voice, using the script at the bottom of this file, while clicking through https://iots-trial.vercel.app.
Option B: upload `deliverables/walkthrough-v3.mp4` (1:25, captioned, no voice) to Loom ("Upload a video") or to Google Drive (share: anyone with the link), and paste that link.

## Repository or files
https://github.com/WrenzLaylo/iots-trial (public; the open pull requests show the build page by page, v3 is PR #9)

## Live demo
https://iots-trial.vercel.app (v3: editorial blog with instant search, clean Locations and Contact)
(v1, closer to the current design: https://iots-trial-classic.vercel.app)

## Upload a file
`deliverables/IOTS-trial-v3-Wrenz-Laylo.zip` (10.3 MB: note, 26-item audit, QA results, desktop + phone screenshots, walkthrough video)
If you send v1 instead: `deliverables/IOTS-trial-v1-Wrenz-Laylo.zip` (4.3 MB)

## Your approach
I started by auditing the three live pages before building anything: their HTML and headers, the WordPress REST API, and screenshots at phone and desktop sizes. That turned up 26 issues (FINDINGS.md in the zip), from branch phone numbers that weren't tappable and hours hidden four pages deep, to missing meta descriptions, a blog H1 that was a post title, and an Español link with no way back to English.

I focused first on what costs calls and search visibility: tap-to-call and visible hours with a live open/closed label on Locations, a Contact page that answers "how do I reach you" right away, and the SEO basics (meta descriptions, heading order, alt text, local business schema for each branch). Then findability on the blog: the 594 posts had no search and no images, so I added instant search with a helpful no-results state, and topic cover art instead of stock photos.

I kept their brand, content and URLs, used only real data from their site, and tested in three browsers with accessibility, keyboard, JavaScript-off and slow-network checks. I worked in Git with a pull request per page.

## Anything else
Time: about 8 hours, including two design passes after reviewing my own first versions.
Versions: the live demo combines an editorial blog (instant search, topic cover art) with clean, quiet Locations and Contact pages. A lighter-touch version closer to the current design is at https://iots-trial-classic.vercel.app
Open questions: Should Contact have a form, and who would answer it? 45 of the 594 posts are in Spanish, mixed into the English blog; together with the Español link that has no way back, it may be worth a proper Spanish section.
Caveats: the preview is noindexed on purpose and has none of your marketing tags (part of the Lighthouse gap). Open/closed labels don't know holiday dates, so cards say "Holiday hours may vary". I used Figtree because Proxima Nova is licensed to your domain.
Also noticed (outside the 3 pages): two Google Tag Manager containers load on every page; the Snapchat pixel sends a literal placeholder instead of an email; the quote button goes through http:// and the redirect duplicates the ZIP; the blog hasn't published since July 5.

---

## Loom script (about 2 minutes, read naturally, don't memorize)
1. (Blog, top) "Hi, I'm Wrenz. This is my rebuild of the blog, locations and contact pages. Before building, I audited the live pages and found 26 issues; the list is in the zip."
2. (Scroll cards) "The 594 posts have no images, so each topic gets its own cover art, and every card shows a reading time."
3. (Type 'sr22') "The blog had no search. Now results appear as you type, across all 594 guides. It ignores accents and punctuation, so 'sr22' finds 'SR-22'."
4. (Type 'insurence') "If nothing matches, you don't hit a dead end: you get a suggestion, popular topics, and a phone number."
5. (Click Coverages, page 2, Back) "Topics filter instantly, with pagination, and Back works because the state is in the URL."
6. (Locations) "On Locations, every branch is now tap-to-call, with its hours and a live open or closed label in Chicago time. Before, hours were four pages away."
7. (Contact) "Contact puts the phone number first, with phone hours, quick links and every branch. I didn't add a form, because someone has to answer it, so that's a question for you."
8. (Close) "I tested it in three browsers, with an accessibility scan, keyboard only, JavaScript off and slow connections. Lighthouse mobile went from the high 20s to 97 to 100. Thanks for watching."
