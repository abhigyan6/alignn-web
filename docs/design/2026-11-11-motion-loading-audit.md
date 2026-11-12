# Alignn motion and loading audit

11 November 2026. Read-only source audit for the frontend redesign, followed by the explicitly assigned loading implementation below. Credentials, user browser sessions and infrastructure were not changed. The parent agent owns browser inspection; browser scenarios below are proposed verification, not completed runtime results. Repository scope: `/Users/abhigyandwivedi/Developer/alignn-web`.

## Direction

This is a daily student opportunity tool: scan, filter, understand fit, save, apply externally and track. Weight Emil's restraint first, Jakub's production polish second; reserve expressive brand motion for an optional first-visit explanation. No motion library is required for the interactions currently identified. More motion is not the solution to unclear navigation or an unexplained product.

The requested output is this scoped Markdown handoff, so the broader motion skill's HTML report/browser-opening step was not run. Its frequency, accessibility and anti-pattern checks informed this audit. No borrowed code/assets or measured-competitor-motion claim is made.

## Findings

| Priority | Evidence in current source | User effect | Repair |
|---|---|---|---|
| P1 | `site-intro.tsx:6–14` sets a first-tab flag before paint, starts a 1300ms dismiss timer; `globals.css:1281–1330` renders a full-screen overlay and holds it fully opaque through70% of a1200ms CSS animation. | Every new tab can visually hide an already ready page for roughly840ms, calculated from CSS, without reflecting a real load. `pointer-events:none` leaves the hidden interface clickable; keyboard/pointer dismissal listeners start only after hydration. | Remove the full-screen wait. Keep the brand mark visible in the real shell and use a small, in-place loader only while a real operation is pending. No minimum hold, artificial progress or entrance gate. If a first-visit flourish survives, it must not obscure controls or delay reading/navigation. |
| P1 | `explore/page.tsx:31–73` increments `attempt` for five-second ranking polls; every request sets `loading=true`. Its render switches all cards to `OpportunitySkeleton` whenever loading. | A useful feed can disappear repeatedly while its match order is recalculated. An upstream error then replaces the useful feed entirely. This is a confirmed code path, not a reproduced live incident. | Separate initial/query loading from background refresh. Keep the last successful feed during same-query ranking polls and show one small status. Keep it on background failure with retry. New-query results may use a stable result-region skeleton, never a whole-page swap. |
| P2 | `auth-provider.tsx:32–36` swaps `/explore` to `DiscoveryLoading` until the Clerk bridge is ready. The mounted Explore then starts its own API loading state. | Two unrelated waits can yield two different skeleton compositions before one usable feed. The public catalog's navigation/search disappears while identity loads. | Preserve the same page chrome, heading, search and filter positions while identity and data settle. Keep the repaired authentication routing intact; only gate protected actions and personalized state as required. Verify slow Clerk and slow API separately before changing this boundary. |
| P2 | `brand-loader.tsx` plus `globals.css:1246–1277` combines infinite1800ms breathing and2400ms orbital rotation. | A state indicator doubles as ambient decoration on repeated account waits. A stalled request can leave two loops running indefinitely. | Retain a static recognizable symbol; use at most one simple functional indicator for pending work. Remove the breathing loop and orbit combination. Expose a readable pending/error/retry state rather than animation alone. |
| P2 | `onboarding.tsx:37–39` focuses the step heading only when `step>1`; Back can return to step1 after removing the focused button. | Keyboard users can lose their place when moving back to education. Adding a transition will not repair that orientation problem. | Focus the current heading after every user-triggered step change in either direction, while leaving initial load focus alone. Keep field errors next to their fields. Keyboard/reduced-motion transitions should be immediate. |
| P2 | Generic `.button:active, button:active` transforms apply to keyboard-activated controls as well as pointers. | A keyboard utility action gets a visual press displacement even though no spatial explanation is needed. | Scope geometric press feedback to pointer interactions; preserve instant visible keyboard focus and state feedback. Do not animate focus rings. |
| P2 | `loading.spec.ts` asserts four skeletons and their presence but not card-to-result geometry, background-poll stability, input focus or stale failure retention. | The test name promises more stability than the assertions establish. The repetitive loading path can pass current tests. | Add the specific interaction/geometry cases below; keep synthetic responses clearly identified as test fixtures. |

The tracker accordion currently uses `hidden` and conditional content (`application-tracker.tsx:103–104`); this is an opportunity for continuity, not a blocker by itself. A readable instant change is preferable to a broken animated accordion. Do not install a library just to animate it.

## Preserve what already works

- CSS reduced-motion handling removes intro, breath/orbit and shimmer movement and suppresses existing transforms/transitions. Every new motion selector must join this contract.
- Hover lift is gated by `(hover:hover)`; touch is not required to discover hover-only controls.
- Existing transitions are short and tokenized: `--motion-fast:140ms`, `--motion-standard:240ms`, `--ease-out:cubic-bezier(0.22,1,0.36,1)`. Extend these rather than introduce a parallel timing system.
- Loader artwork and skeleton geometry are hidden from assistive technology, with a single `role=status` message and busy container.
- Current async effects abort on unmount/query replacement. Preserve that cancellation and the latest-request-wins rule.
- The onboarding heading already supports programmatic focus. Existing tracker buttons expose expanded/control state. Preserve these semantics when changing visuals.

## Exact motion contract for implementation

Values below are proposed design targets, not measured timings. Use CSS transitions first. Keep transform/opacity motion off layout properties; do not animate `top`, margins or each result's height. No scroll hijacking, parallax, pointer followers, staggered search-result entrances, confetti, animated numeric counts or default spring bounce.

| Surface/action | Trigger and timing | Interruption/accessibility rule |
|---|---|---|
| Page shell, headings, source facts and list text | Paint immediately; no entrance animation. | Content never waits for choreography. Browser Back and keyboard navigation remain native. |
| Button/category hover | Color/border140ms; no card scaling. | Hover treatment only on devices with hover. Active category state updates immediately; no delayed selection. Keyboard focus is instant. |
| Pointer press | Existing140ms feedback, at most1px displacement, without changing control dimensions. | Suppress geometric feedback on `:focus-visible`/keyboard and reduced motion. Rapid presses retarget; never queue. |
| Opportunity cards | Color/border140ms, optional shadow240ms. A2px lift is the maximum, not a requirement. | No delayed grid entrances; titles remain readable. Touch gets the same visible actions without hover. |
| Save/remove feedback | Immediate saved state after a successful server response; bookmark fill/color140ms, one polite text confirmation. Keep button/icon width stable. | Pending state disables duplicate requests, not the whole card. Failure restores truthful state and offers retry. No optimistic success without rollback or announcement. |
| Initial discovery data | Skeleton uses the final result-region structure and responsive column count. Existing1800ms shimmer may remain while genuinely pending; no artificial hold. | `aria-busy` on the result region, one concise status. Reduced motion uses static skeletons. Result/error replaces it immediately when ready. |
| Same-query ranking/refresh | Keep current cards and scroll position. At most a small inline static/functional activity indicator; no list fade or skeleton replacement. | Background failure keeps data with an “Unable to refresh” message and retry. New results do not seize focus. |
| New search/category/page | Keep shell/controls mounted. Show pending state only within results; do not relabel an old mixed feed as the new category. No stagger. | Abort superseded requests; late replies cannot win. Move focus to the result heading only after explicit pagination if needed, never after automatic refresh. |
| Mobile filters, if introduced | Enter240ms with opacity and up to16px vertical translation; exit120ms. Preserve an existing240ms standard token and add an exit token only if needed. | Use a native dialog or accessible existing primitive for focus trapping, Escape/backdrop close and returning focus. Keyboard/reduced motion opens/closes immediately. No full-page horizontal swipe or scroll trap. |
| Onboarding step | Pointer-triggered content may use opacity/at most6px translation over140–240ms; progress indicator may change via `scaleX`240ms from the left. | Heading focus and semantic current-step state update immediately. Keyboard/reduced motion is instant. Back preserves inputs. Never add a fake completion percentage. |
| Résumé upload | Button-local “Uploading…” while bytes transfer; “Security scan pending” only after the backend queues the scan. | No invented percentage, scanning animation that implies extraction, or claims of résumé matching. Parsing is currently unconnected. Always allow the existing optional skip route. |
| Tracker expand/save | Instant expansion is acceptable. If implemented, open240ms and close120ms; inner content remains stable, no per-line animation. Save uses a local pending label and one confirmation. | Do not focus unmounted content during exit. Rapid open/close must settle to the last requested state. Keyboard/reduced motion remains instant. |

A background refresh and a new query are different states. Recommended state model: `initialPending` (no result yet), `queryPending` (different search/filter/page), `refreshing` (same successful query), `ready`, `empty`, `fatalError` (no usable result) and `refreshError` (usable prior result remains). This should live in request state rather than be inferred from card count.

## Browser verification to add/run

Root should run these against the redesigned app at360,390,768 and1440 CSS pixels, plus the user's current319px viewport. Use the existing Playwright installation and explicit fixture responses; these tests do not prove real Clerk onboarding or production behavior.

1. **No artificial welcome gate:** fresh tab/empty session storage, immediately usable heading and navigation. Repeat with storage unavailable and reduced motion. No clickable region may be visually covered by decorative loading.
2. **True initial skeleton:** defer a fixture opportunity response, assert result-region busy state and one status message, then release. Search/category controls stay in place; skeletons disappear on success/error without minimum delay. Compare card region edges before/after, not only skeleton count.
3. **Background ranking stability:** first response contains a fixture opportunity and `PENDING`; delay the five-second poll. Assert that card remains visible, its source action stays correctly associated, focus and `scrollY` stay stable, and no replacement skeleton appears. Resolve to fresh ranking. Repeat until the retry cap.
4. **Background error retention:** same setup, fail the refresh. Assert the existing card remains, an inline refresh error appears, and retry does not blank it. A genuine first-load error still gets an explicit error/Retry state.
5. **Race/latest query:** rapidly select categoryA thenB; fulfillB first andA late. OnlyB results and active control remain. Test search input Enter and pointer selection. Assert no uncontrolled entrance animations or queued transitions.
6. **Reduce motion:** emulate before navigation; assert no running decorative animations on intro, loader, shimmer or panels and no animated scrolling. Repeat a category change, save, onboarding step and filter dialog. Content and functional confirmation remain available.
7. **Keyboard orientation:** tab through navigation/search/categories; activate with Enter/Space. Focus ring is immediate and not translated. Onboarding forward and Back focus the new heading without losing saved inputs. Filter dialog Escape returns focus to its trigger.
8. **Save/track feedback:** defer success, assert only the action is pending, no duplicate request. Then success/failed response with truthful final state and one polite announcement. Tracker open/close rapidly should end in the last state; closing cannot leave invisible focusable fields.
9. **Responsive stability:** long titles, empty results, mixed date availability, slow identity and slow data. No horizontal overflow, offscreen focused element, bottom-sheet content hidden by keyboard, or CTA covering page content.

Prefer deterministic interaction tests over arbitrary sleeps. No requirement to make every conditional render animate. A useful measurement pass may sample frame/layout cost on an actual constrained device later; this code audit does not establish60fps or a latency SLO.

## Skills from the user's starred collection

- **[Emil Kowalski's skills](https://github.com/emilkowalski/skills):** best fit for product interaction restraint and implementation. His `animate` guidance makes motion conditional on frequency/purpose, reuses existing tokens and favors CSS before a new dependency. Use `improve-animations`/review guidance for the audit stage and `animate` only for a defined interaction. This recommendation is based on the inspected [source skill](https://github.com/emilkowalski/skills/blob/main/skills/animate/SKILL.md), not a popularity claim.
- **[Motion Transplant](https://github.com/lakshya1282/motion-transplant):** appropriate only after selecting one specific reference effect worth reproducing. Its [protocol](https://github.com/lakshya1282/motion-transplant/blob/main/SKILL.md) calls for evidence and a clean-room rebuild using our content/assets. It is unnecessary overhead for basic focus, busy states or filters. Do not claim measured curve fidelity unless capture/rebuild measurements were actually performed; adapt its browser snippets to the host's permitted API rather than running injected mutation scripts blindly.
- **[Motion Graphics Skills](https://github.com/charlie947/motion-graphics-skills):** its [README](https://github.com/charlie947/motion-graphics-skills/blob/main/README.md) describes title sequences, launch/promo loops and video exports. Useful for a future product-launch video or deliberately scoped landing explainer; not a runtime dependency or reason to add an8-second video to every app load. No installation/execution was performed.

## Implementation ownership suggestion

Root keeps `explore/page.tsx`, global tokens and shared shell ownership to avoid competing state models. A scoped follow-up can assign loading components plus `loading.spec.ts` to one implementer **after** the new layout/classes and no-overlay decision are fixed. Shared `globals.css` edits should remain with root or be supplied as a reviewed patch. Tracker/onboarding focus and success behavior can be tested with their owning screen changes. No app changes were made by this audit.

## Scoped implementation follow-up

On the parent agent's explicit assignment, changed only `site-intro.tsx`, `brand-loader.tsx`, `opportunity-skeleton.tsx`, `account-loading.tsx`, `discovery-loading.tsx`, new `loading.module.css`, and `tests/loading.spec.ts`. The old SiteIntro is now a compatibility no-op/empty script while root removes its layout imports. The functional loader has a static brand mark and one constant-speed pending ring; no breathing/orbit combination. Short skeleton cards have logo/category, title, metadata, skills and footer placeholders, one card-level shimmer, and reduced-motion static alternatives. There is no minimum loading delay. Discovery fallback uses the confirmed product heading/subtitle; account loading copy describes actual loading.

Formatting and scoped diff whitespace checks passed. Browser tests were attempted in desktop/mobile with a temporary headless Chrome profile and `/tmp` outputs; the shared dev build was in an intermediate state and showed missing `./workspace.module.css` from `application-tracker.tsx`. This blocked runtime validation rather than establishing a loader regression or pass. Root was informed; rerun `playwright test tests/loading.spec.ts --project=desktop --project=mobile` after the owning workspace implementation compiles. No browser pass is claimed here.

## Synthetic account interaction verification — 12 November 2026

At the parent agent's explicit request, created a temporary local `/review-fixture` page rendering the existing production Onboarding or Workspace component with a typed, clearly synthetic profile. Its visible banner read “Synthetic UI review only — no real account or backend writes”. Fresh headless Chrome contexts used390×844 and1440×1000 viewports with reduced motion. Every browser `/api/v1/**` request was intercepted; an unspecified endpoint would return a synthetic501 rather than reach the real API. No real Clerk sign-in, credential inspection, resume upload or backend write was performed.

The completed script `/tmp/alignn-account-review.mjs` and results `/tmp/alignn-ui-review/account-review-results.json` record six behaviour groups at each viewport (12 groups total). Each context intercepted18 application API requests, including seven writes to in-memory synthetic fixtures, with zero unmatched requests:

1. Empty education submission associates four errors with their fields, sets invalid state and focuses the first invalid college field.
2. Filling education and moving forward/Back preserves the college, degree and graduation draft and focuses the appropriate step heading in both directions.
3. Skill search narrows the displayed choices, selected Python/React skills survive searches, interest suggestions and Remote format generate the expected controlled fixture payloads.
4. Optional resume can be skipped; completion posts to the intercepted fixture, routes to `/explore`, and never creates a file/upload request.
5. Saved Active/Closed filters show the correct active or preserved closed record. The shared bookmark action issues an intercepted DELETE and removes only that fixture record.
6. Manual application stage/note updates post the expected synthetic event, refresh the visible history, and preserve a non-overflowing application layout.

Captured and visually opened all ten full-page screenshots: `/tmp/alignn-ui-review/onboarding-{390,1440}.png`, `onboarding-resume-{390,1440}.png`, `saved-{390,1440}.png`, `saved-closed-{390,1440}.png`, and `applications-{390,1440}.png`. The first run required correcting an overly exact test locator for a select wrapped in a label; that was a harness locator correction, not an application change. The final run passed all requested scenarios. No material clipping or overlap was found in these captures; the visible Next.js development indicator is development chrome, not shipped application content.

The synthetic route's `page.tsx` and empty directory were deleted after verification and are not shipped or committed. All account components remained unchanged by this verification task; only this evidence was appended. Application-tab coverage uses the temporary fixture query because actual `/workspace` remains protected. This proves the tested components against controlled UI responses; it does **not** establish real Clerk authentication, server guards, end-to-end persistence, public upload/scanner behaviour, a production deployment or performance/accessibility compliance.
