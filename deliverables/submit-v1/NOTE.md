Preview: https://iots-trial-classic.vercel.app (noindexed on purpose; robots.txt stays open so Google can see the noindex)

What I tested
- Chrome, Firefox and Safari's engine at 320-1440px; axe accessibility scan (0 issues); keyboard-only use.
- Every link and phone number, the ZIP quote box, JavaScript off or failing, open/closed labels from another time zone, and structured data (0 validator errors).
- Lighthouse mobile: performance 99-100 vs 26-27 live, accessibility 100 vs 87-95 (partly because the preview has no marketing tags).

Improvements
1. Locations: tap-to-call for every branch, hours on each card, and a live open/closed label in Chicago time. Hours used to be four pages away.
2. SEO basics: meta descriptions (none before), a real blog H1 instead of the latest post's title, heading order, alt text, and branch schema.
3. Contact: fixed the hero overlap and blank gaps, and added the branches plus quick links for payments, claims and roadside help.

Also found: the Español link leads to one Spanish page with no way back to English. Question: should Contact have a form, and who would answer it?

Tools: Claude Code, Python (your WordPress REST API), Playwright, axe, Lighthouse, GitHub, Vercel.
