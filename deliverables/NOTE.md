Preview: https://iots-trial.vercel.app (noindexed on purpose; robots.txt stays open so Google can see the noindex)

What I tested
- Chrome, Firefox and Safari's engine at 320, 390, 768 and 1440px: no sideways scrolling, no script errors.
- Accessibility: axe scan with zero issues, keyboard-only navigation with a visible focus ring everywhere.
- All 88 links and every phone number, the ZIP quote box (valid and invalid ZIPs), the pages with JavaScript off, the open/closed labels from another time zone, and the structured data (schema.org validator, 0 errors).
- Lighthouse mobile: performance 99-100 vs 26-27 on the live pages, accessibility 100 vs 87-95. Part of that gap is that the preview has none of your marketing tags.

Improvements and why
1. Locations: every branch is tap-to-call and shows its hours with a live open/closed label in Chicago time. Before, branch numbers weren't tappable and hours were four extra pages away.
2. SEO basics: meta descriptions (there were none), a real H1 on the blog instead of the latest post's title, correct heading order, alt text, and local business schema for each branch.
3. Contact: fixed the hero overlap and blank gaps, and added the branches plus quick links for payments, claims and roadside help.

Also found: the Español link leads to one Spanish page with no way back to English, marked as English, with no hreflang. And a question: should the contact page have a form? If so, who answers it and where should leads go? I have the full audit (26 findings) if useful.

Tools: Claude Code, Python (content pulled from your WordPress REST API), Playwright, axe, Lighthouse, GitHub, Vercel.
