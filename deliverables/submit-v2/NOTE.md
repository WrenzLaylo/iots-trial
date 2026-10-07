Preview: https://iots-trial.vercel.app (noindexed on purpose; robots.txt stays open so Google can see the noindex)

What I tested
- Chrome, Firefox and Safari's engine at 320-1440px; axe accessibility scan (0 issues); keyboard-only use.
- Every link and phone number, the ZIP quote box, JavaScript off or failing, open/closed labels from another time zone, structured data (0 validator errors), and search with typos, accents and no matches.
- Lighthouse mobile: performance 97-100 vs 26-27 live, accessibility 100 vs 87-95 (partly because the preview has no marketing tags).

Improvements
1. Blog search: results as you type across all 594 guides, with suggestions instead of a dead end. The blog had no search.
2. Locations: tap-to-call for every branch, hours on each card, and a live open/closed label in Chicago time. Hours used to be four pages away.
3. SEO basics: meta descriptions (none before), a real blog H1, heading order, alt text, branch schema, and lang="es" on the 45 Spanish posts.

Also found: the Español link leads to one Spanish page with no way back to English. Question: should Contact have a form, and who would answer it?

Tools: Claude Code, Python (your WordPress REST API), Playwright, axe, Lighthouse, GitHub, Vercel.
