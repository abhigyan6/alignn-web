# Alignn frontend system audit

11 November 2026. Source baseline: `b49ce70`, before the current redesign. Line references in the findings describe that baseline, not later edited files. Scope: source inspection of the current Next.js/React/custom CSS interface and selected doctrine from the user's Design & Frontend star list. No credentials, private account state or browser session was inspected. This audit is not a measured accessibility pass or a full signed-in visual acceptance result; the primary agent owns browser verification.

## Product truth the screens need to show

A student provides education, skills and interests, optionally uploads a private resume, then discovers relevant Indian external opportunities, checks the original requirements, saves a shortlist and records application progress. Profile fit is evidence overlap, not eligibility or selection probability. Resume upload/scan exists; resume text extraction does not. Event hosting, teams, internal applications and judging are outside scope.

## Prioritised findings

| Priority | Before / evidence | After | Why |
|---|---|---|---|
| P1 | `app/page.tsx:1-24` says Coming soon, while `components/app-navigation.tsx:12-17` removes all navigation at `/`. There is no discovery/sign-up CTA on that page. | Replace the dead end with a real product entry and working Browse opportunities/Create profile paths. | Someone opening the domain cannot discover the working product or understand its purpose. |
| P1 | `components/onboarding.tsx:63-68,453-454` completes into `/workspace`; its first payload is saved opportunities and tracking, commonly empty for a new account. | Complete into `/explore` with profile-informed discovery; editing can still return to the same useful destination. | The payoff for giving profile information should be relevant opportunities. |
| P1 | `components/opportunity-card.tsx:26-62` ignores `status`; `app/opportunities/[id]/page.tsx:105-125` always renders active application/save/track actions. Closed saved records are now deliberately returned by the backend. | Show a Closed state, retain the original details/source link, and distinguish historical reading from a live Apply CTA. | Preserving history physically is insufficient if the interface represents an expired item as open. |
| P2 | `app/explore/page.tsx:31-43,238-243` sets loading on every five-second ranking poll and replaces real cards with skeletons. | Separate first load/filter change from background re-ranking. Keep existing results stable and communicate refreshing once. | A revalidation should not repeatedly blank the screen or resemble the earlier auth flicker. |
| P2 | `app/explore/page.tsx:81-178` spends two major regions on motivational explanation, then another sidebar before the results. The wording says little about India, external sources or why these results fit. | Put the search/results task first, with one short product explanation and profile-based context. Remove the second instructional rail. | Useful opportunity content should lead the operating screen. |
| P2 | `components/opportunity-card.tsx:28` makes the entire card one link; saving requires a second screen. Company/category/skills/footer metadata mostly share the same small green/grey treatment. | Use an article with a meaningful title link, a distinct Save control and a restrained information hierarchy. Include actual dates/source/status without inventing employer logos or fit scores. | Shortlisting is a frequent action and should not require inspecting every detail first. |
| P2 | `app/opportunities/[id]/page.tsx:134-175` puts fit behind a manual button after the full description, then exposes raw factor keys and percentages. Event start/end fields are not presented as a date block. | Present a concise date/source summary and readable profile-match factors. Keep unknown eligibility explicitly unknown and use the original requirements as authority. | The core matching value and time meaning should be understandable before a long description. |
| P2 | `components/workspace.tsx:18-21,47-54` labels any `/me` or `/me/saved` failure as Sign in to continue; one saved-feed failure replaces the whole workspace. `components/onboarding.tsx:177-181` has a bare error with no recovery. | Differentiate authentication errors from network/server errors. Offer retry and retain unaffected content. | The current recovery instructions can send a valid signed-in account back toward login unnecessarily. |
| P2 | `components/onboarding.tsx:386-405` asks for comma-separated interests and displays raw ANY/REMOTE/HYBRID/ONSITE choices; a large skills catalogue renders all checkboxes without search. | Human-readable work-mode labels, labelled interest examples/limits, searchable existing skills, and persistent in-progress answers. | Profile setup should be a short understandable task, not taxonomy entry. |
| P2 | `globals.css:5-16,395-400,1193-1197,1524-1526` declares separate token clusters; auth hardcodes a second paper/ink palette, and `auth-shell.tsx:4-23` duplicates values outside CSS. The 1,917-line stylesheet layers repeated `.hero`, `.event-grid`, `.detail`, `.workspace` rules and several late breakpoint patches. | One semantic colour/type/space/radius/motion contract; scoped auth/onboarding modules; replace obsolete rules instead of appending another layer. | Small local fixes currently have unpredictable cross-screen effects. |
| P2 | `globals.css:697-710` makes tablet auth a 460px story above a >=620px panel. On narrow screens the story heading disappears (`752-759`), while onboarding hides its only h1 (`1076-1078`). | A compact mobile auth entry and visible task heading, with the larger explanatory story reserved for wide viewports. Preserve clear heading structure. | Form access and purpose must survive reflow rather than disappear into decorative chrome. |
| P3 | Cards use 11px categories/skills/footer and 12px company text (`globals.css:1687,1703,1726,1737`), while repetitive title and panel treatments flatten priority. | Body/control text >=16px on mobile; supporting metadata typically12-14px; real title hierarchy and readable source/deadline labels. | Small type reduces scanability even when colour contrast happens to be adequate. |
| P3 | `components/account-loading.tsx:24-32` uses form-field skeletons for both onboarding and workspace, although the workspace is a saved feed and tracker. | Skeleton geometry follows the destination screen; one live status announcement. | Loading should preserve the screen's structure rather than teach the wrong layout. |

The code already provides useful foundations: a skip link, visible focus outline, real labels, checkbox semantics, ARIA step/current states, request cancellation, user-triggered external links, working retry actions in the tracker, shared cards and reduced-motion rules. Preserve these while redesigning.

## Shared design contract

Direction confirmed by the primary agent: a polished light student opportunity product with Manrope, neutral canvas, white surfaces, dark ink, forest actions, pale lime emphasis and restrained lilac category accents. This audit does not prescribe another competing visual world.

- One shared colour vocabulary: `--paper`, `--surface`, `--ink`, `--muted`, `--line`, `--accent`, `--accent-soft`. Category/status colours are separate semantic roles, never alternate primary-action palettes. Auth provider styling must consume the same variables.
- Spacing follows a small4px base scale; nearby label/help/control elements group tightly, sections separate clearly. Controls and panels have distinct radii. Borders define normal surfaces; elevation is reserved for overlays/popovers.
- Every interactive component has intentional default, hover, keyboard focus, active, disabled, pending, error and selected states where applicable. Keep focus visible. Loading does not disable unrelated navigation or erase settled content.
- All common controls maintain >=44px touch targets; inputs stay16px on mobile. Use native controls when they fit the task; a custom combobox is justified only with complete keyboard, focus, announcement and typeahead behaviour.
- Main navigation names the actual tasks: Discover, Saved and Applications, with profile/account access separate. Existing workspace anchors/tabs can express those destinations without new backend features. Do not create empty feature routes to fill the nav.
- Discovery uses real categories/search/sort currently supported by the API. Do not show decorative location/remote filters that only filter the current page or do nothing. With paginated data, label a count as “Showing12” rather than invent a total.
- An opportunity summary has one wrapping title, organization, category, location/format, sourced application cutoff, event dates when known, provenance and save state. Unknown is a valid visible value. Closed histories remain recognisable.
- Details distinguish source facts, inferred related skills, personal fit and unknown eligibility. “Related skills” is safer than claiming every inferred keyword was an organizer requirement. Original-source application remains external and is separate from manual tracking.
- Profile setup is Education → Skills/interests → Optional resume → Discover. Keep entered values when going back. Show what the data changes without promising automated resume parsing.
- Auth is a shared layout for sign-in/sign-up, with a short explanatory story on wide screens and immediate form access on mobile. Avoid a second oversized brand block under the header. Preserve the repaired Clerk/session/server redirect behaviour.
- Use stable DOM and focus when state changes. Step headings receive focus when changing steps; errors explain recovery beside the relevant field or in a focused summary. Upload statuses use understandable labels rather than raw API enum strings.

## Responsive and state verification

Verify the actual user viewport plus320/360/390/768/1024/1440px. These are check samples, not the source of breakpoints: place breakpoints when the content needs another composition. Test200% zoom, reduced motion, keyboard-only navigation, long titles/organization names, zero results, multiple pages, signed-out matching, failed initial load, failed revalidation, source-unknown dates, closed saved records and upload failure/pending scan. A passing screenshot cannot prove keyboard behaviour; a passing scripted gate cannot replace looking at the render.

## Starred-source review

| Source inspected | Useful contribution | Proportionate use / caution |
|---|---|---|
| [Emil design engineering](https://github.com/emilkowalski/skills/blob/main/skills/emil-design-eng/SKILL.md) | Ask whether motion belongs at the interaction's frequency; explicit transition properties; fast feedback; interruptible state changes; hover only where supported; reduced motion. | Good primary interaction craft reference. Avoid adding springs/blur just because recipes exist. |
| [UX/UI Agent Skills doctrine](https://github.com/plugin87/ux-ui-agent-skills/blob/main/AGENTS.md) | Semantic tokens, one theme, eight states, one clear visual lead, mobile base styles, render-and-click verification and evidence-bounded claims. | Inspect narrow `design-tokens`, `design-component`, `ux-writing`, `design-qa` and `a11y-audit` skills under `.claude/skills`. Do not import hooks or all26 workflows. Its “never native select” and universal display-size rules are house style, not necessary product requirements; replacing native behaviour requires stronger verification. |
| [Anti-slop UI](https://github.com/miqdadbadjuber/anti-slop/blob/main/skills/antislop-ui/SKILL.md), [mobile layout](https://github.com/miqdadbadjuber/anti-slop/blob/main/skills/antislop-layoutmobile/SKILL.md), [core](https://github.com/miqdadbadjuber/anti-slop/blob/main/antislop.md) | Purpose behind techniques, no invented proof, avoid sterile defaults, separate mobile compositions, preserve content instead of clipping and keep primary navigation reachable. | A filter cannot supply art direction. The core has its own installation/mode/asset approval ceremony; reading this candidate is not authorization to append instructions, install hooks or adopt every absolute stylistic ban. |

These repositories were reviewed as primary-source doctrine. They were not installed or executed by this subagent. No quality score, complete WCAG claim or measured motion-fidelity claim is made.

## Migration order

1. Confirm the product sentence and primary destinations, then replace the coming-soon dead end and correct the post-onboarding destination.
2. Define shared tokens and screen/component contracts; maintain auth/session behaviour while replacing visual wrappers.
3. Rebuild discovery/cards/detail around source facts, shortlisting and stable refresh. Add explicit closed history treatment.
4. Rebuild saved/tracking and profile setup with purposeful empty/error/loading states.
5. Batch visual/keyboard/mobile checks, repair the observed defects, then record the final system and outstanding product gaps. Do not deploy while local acceptance is still open.


## Assigned implementation checkpoint

The auth/onboarding portion was implemented by this subagent in four scoped files only: `components/auth-shell.tsx`, `auth-shell.module.css`, `onboarding.tsx` and `onboarding.module.css`. Shared globals, Clerk/session bridge and server guards were not edited.

- Shared variable-driven auth layout and Clerk appearance map; wide-screen explanatory journey and compact mobile form entry, with no duplicate brand header. Existing `.auth-shell`, `.auth-panel` and `.auth-clerk-root` remain compatibility hooks, not a global theme dependency.
- Onboarding keeps in-progress answers while changing steps, focuses the step heading and invalid fields, provides retry after an initial data-load error, offers skill search and real interest suggestions, labels work formats and scan states in plain language, and completes to `/explore`.
- Resume upload still uses the existing backend ticket/upload/complete flow. The interface explicitly states that extraction is unavailable and that selected skills/interests drive matching. No new auth logic or backend feature was added.
- Verification: `tsc --project apps/web/tsconfig.json --noEmit --incremental false` passed, scoped Prettier check passed, and scoped `git diff --check` passed. The npm wrapper initially could not write its incremental cache under this agent's exact-file write grant, so the same compiler was rerun without cache writes. Browser/keyboard/mobile verification belongs to the primary agent's integration pass and is not claimed here.
- Clerk CSS-variable theming was checked against [official Clerk appearance documentation](https://clerk.com/docs/js-frontend/guides/customizing-clerk/appearance-prop/variables). Current browsers support it; the documentation notes browser-version constraints, so older-client acceptance requires its own check.
