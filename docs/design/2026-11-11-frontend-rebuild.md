# Alignn frontend rebuild contract

User confirmed the product journey and delegated design decisions on 11 November 2026. The whole frontend is authorized for redesign, current authentication/backend contracts preserved. Read `apps/web/PRODUCT.md` for product truth. This is a focused build with parallel scoped research/implementation, not another Superpowers process.

## Direction

A student opportunity desk: structured enough to compare applications, optimistic enough for exploration. Recognizable Alignn loop, Manrope, light neutral canvas, white working surfaces and forest actions. Pale lime marks the personal-profile invitation; lilac and warm neutral category treatments carry category information. Public landing explains the mechanism through real listings. The daily discovery screen is compact and factual, without promotional sidebars. No dark SaaS dashboard, generic mock metrics, sponsor logo wall or artificial splash screen.

Palette: canvas #f7f8fa; surface #ffffff; ink #182821; muted #65726c; border #e1e6e1; forest #145640; supporting lime #d9eeaa. Color roles/tokens are centrally defined; category colors never compete with primary actions. Implemented typography uses a 16px body (15px on compact mobile), 12px critical card deadline/source metadata, 17–18px card titles, 29–42px app headings and 34–62px landing headings. Keep negative tracking within -.04em. Panels use a 16px radius and controls 10px, with compact category controls.

## Layout and task hierarchy

- Header: brand, Discover, Saved, Applications, Profile; signed-out account actions. Mobile compact top brand/account and visible primary task navigation with reserved space.
- Home: readable product promise, Explore and Create profile actions, branded connecting-loop treatment, real sourced opportunity preview and concrete profile/matching explanation. No Coming Soon dead end or fake feed.
- Discover: brief title, search, category buttons, one optional profile invitation, results/sort, real card grid. No nonfunctional filters. URL category/search links work from home; repeat ranking polls retain useful cards.
- Card: category/organization monogram, real organizer, wrapping title, location/work mode, available inferred/listed skills, true deadline, source, distinct save control. Closed saved records clearly closed; no invented fit percentages. No full-card nested link/button interactions.
- Detail: back navigation, category/organization/title, facts grid and dates; readable plain-text source description, honest fit/eligibility explanation; reachable source apply/save/manual tracking actions. Closed records show history state and source information instead of active Apply.
- Saved/Applications: distinct workspace tabs backed by existing endpoints, helpful empty/retry states, no fabricated account metrics.
- Auth/setup: same system and scoped form styling, compact progress, field-level instructions, optional resume truth, completion directly to discovery. Existing protected routes and session logic remain intact.

## Motion and state contract

No artificial full-screen delay. Initial pending work uses accurately sized skeletons and a status announcement. Existing cards remain during background polling; updating is a quiet status. Focus and keyboard interactions are immediate; hover/press feedback~140ms, drawers~200ms ease-out. Reduced motion removes spatial effects and shimmer. Animation must explain a state change or navigation, never hide available content.

## Skill/source selection

Consulted the user's complete12-repository Design & Frontend list. Selected pinned Emil design engineering and Motion Transplant instruction packages; consulted anti-slop copy/mobile/UI doctrine and UX/UI Agent Skills references via the audit agent. Installed skills are instruction sources, not application dependencies. No hooks or bundled candidate scripts are enabled. Existing Impeccable context identified the missing product record; frontend implementation uses the focused source-guided design contract above, avoiding overlapping full conceptual workflows. Any source motion used must be clean-room, attributed and measured/inferred labels retained.

## Verification

TypeScript/production build; meaningful Playwright checks for real API discovery and source link, query/category, clear/retry, closed/save behavior, consistent auth shells, background refresh retention, reduced motion, keyboard and mobile overflow at319/360/390/768/1440. Signed-in components may use explicitly synthetic fixtures; do not claim a real Clerk session was tested unless it was. Review actual browser renders, desktop and mobile, then fix concrete issues. No deployment or app main push in this change.
