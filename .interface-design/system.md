# Alignn interface system

The user approved the core journey on 11 November 2026: discover Indian external opportunities, create a student profile with an optional private resume, inspect profile-based fit, save, apply at the original source and track progress. The prior coming-soon/motivational layout was rejected. `apps/web/PRODUCT.md` is product truth.

## Visual contract

Manrope is the single family. Light canvas `--paper:#f7f8fa`, white `--surface`, ink `#182821`, muted `#65726c`, line `#e1e6e1`, forest action `--accent:#145640`, pale-green supporting surfaces `#edf4e9`, lime `#d9eeaa` and category lilac `#eeebfa`. Semantic tokens are in globals.css, not per-page theme overrides. Clerk receives literal matching values because its own --accent shadows the app token; auth module resolves namespaced --alignn-auth-* aliases.

Typography: body 16px (15px compact mobile), controls>=16px on mobile, app heading 29–42px, landing heading 34–62px, card titles 17–18px. Critical card deadlines/source metadata 12px. Negative tracking no tighter than -.04em. Layout max 1280px including 40px desktop gutters, 20px mobile gutters. Panel 16px radius; control 10px; 4px base spacing. Cards use borders, the landing source preview has a single restrained elevation.

## Tasks and components

Navigation: Discover / Saved / Applications / Profile. Public home explains the product and uses actual API listings; no invented metrics, sponsor/testimonial rows or mock recommendations. Category/search links preserve query state. Profile completion and returning account routing land in Discover.

OpportunityCard is an article with a stretched detail link and a distinct 44px bookmark control, shared with Saved. It preserves unknown organizer attribution as Via [source], wraps long titles, shows known format/skills/true deadline and labels closed history. Saved supports active/closed filters. Applications stays manual and distinct from saved; notes/history are private API-owned records.

Details separates source description/fit evidence from apply/save/manual tracking. Source dates are displayed in IST and different time fields stay distinct. Closed listings have no active Apply/Track action. Fit failure/recovery stays adjacent to the fit button on mobile. There is no invented list-level fit percentage or presumed external eligibility.

Auth and onboarding use scoped modules/shared tokens. New profile setup has education, skills/interests and optional resume steps, field errors/focus, controlled back navigation and retry states. Resume upload/scan exists; extraction/AI suggestions are unfinished and never claimed by copy.

## Motion and feedback

No artificial first-tab splash or minimum wait. A static brand mark plus one pending ring appears only for real pending work. Short-card skeletons reserve content space. Background matching polls retain existing cards. Interactions use 140ms color/border feedback; no scroll hijacking or per-card entrance cascade. Reduced-motion disables ring/shimmer/spatial effects. Keyboard focus is always visible and does not wait for animation.

## QA boundaries

Responsive public-page checks cover 319/360/390/768/1440px, real API discovery and separate synthetic fixture scenarios. Anonymous Clerk form visibility/contrast is verified without entering credentials. Account UI may be exercised in a temporary clearly labelled fixture harness with every API call intercepted; those checks are not a real authenticated provider journey. Production deployment is a separate gate.
