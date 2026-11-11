# Alignn product completion

This checklist follows the user's 11 November direction to finish the app locally before returning to AWS deployment. The older November 3 spec and plan include event hosting, teams, registration and judging. Later instructions removed that scope. Those domains must not be restored by following the old checklist.

The core journey is account creation or sign-in, education and interests, optional private resume, user-confirmed profile information, personalized discovery, saved opportunities, external applications and application tracking. Events and hackathons are external opportunities.

## 1. Establish the working baseline

- [ ] Bring up the existing local app and PostgreSQL without overwriting user data.
- [ ] Reproduce and record the actual signed-in login/onboarding flicker, including redirects and failed requests.
- [ ] Verify new, incomplete, returning, signed-out and expired-session journeys.
- [ ] Verify that profile edits and onboarding completion persist after reload and sign-out.

Existing evidence from the recovery audit: 81 backend tests and ten signed-out auth browser checks passed. Those checks do not establish signed-in correctness. A Clerk refresh-loop warning remains unresolved. Recovery fixes are on PR #2 and are not established as deployed.

## 2. Consolidate the design system

- [ ] Inventory all screens, existing tokens and component states, with screenshots before visual changes.
- [ ] Consolidate the current blue global accent, green auth palette and onboarding overrides into a consistent brand system.
- [ ] Use one shared scale for typography, spacing, colors, controls, cards, feedback, loading and focus states.
- [ ] Apply the system across auth, onboarding, discovery, details, workspace and tracking.
- [ ] Preserve the Alignn brand symbol, readable Manrope typography and existing product copy unless a flow requires clarification.

## 3. Repair responsive behavior

- [ ] Review every screen at 360, 390, 768 and 1440 CSS pixels.
- [ ] Fix overflowing cards, filters, dialogs, long text, navigation, form controls and application history.
- [ ] Verify keyboard focus, 200 percent zoom, reduced motion and loading/error/empty states.
- [ ] Exercise mobile onboarding and resume upload, not just static screenshots.

## 4. Make discovery data dependable

- [ ] Recheck Remotive's source terms and the current feed contract before live fetching changes.
- [ ] Verify fetch, normalization, deduplication, updates, source attribution and stale/closed listing handling through the actual worker and scheduler.
- [ ] Choose and verify permitted sources covering events, hackathons and internships. Current code has one Remotive feed and does not establish full category coverage.
- [ ] Record unavailable deadlines, eligibility and geography as unknown rather than inferring unsupported facts.
- [ ] Exercise source failures, incomplete feeds, retries and ranking updates.

## 5. Complete the agreed product capabilities

- [ ] Implement safe resume text extraction after scanning, then show suggested profile changes for user confirmation. This is currently missing.
- [ ] Verify profile, interests and confirmed skills influence matching with understandable explanations.
- [ ] Verify search/filter/sort/pagination, saved opportunities, external application links and tracking history end to end.
- [ ] Compare remaining career guidance and notification requirements with the original repository and record their exact contracts before implementation.
- [ ] Label incomplete capabilities clearly until implemented and verified.

## 6. Release gate

- [ ] Repeat relevant authorization, private upload, ingestion, job retry and migration tests against real PostgreSQL.
- [ ] Run the complete new-user and returning-user journeys with the real configured identity provider.
- [ ] Review desktop/mobile screenshots and eliminate placeholder or misleading success states.
- [ ] Match frontend, backend, worker and scheduler revisions and rehearse deployment and rollback.
- [ ] Resume AWS deployment only after local product acceptance. Hosting availability alone does not establish product completion.

No traffic measurements, security assurance or compliance claim is made by this checklist. Provider limits and source terms require current verification when their work begins.

## First UI repair checkpoint

Discovery long-title clipping was reproduced at 360, 390 and 768px, then fixed with wrapping and shrinkable grid tracks. Eight browser checks passed across four widths and two browser profiles. Match polling now resets when the query/category/sort changes, and stale discovery requests are aborted. The shared green palette is consolidated as a first design-system pass in `.interface-design/system.md`. The full signed-in and mobile journey remains pending. Antigravity returned a focused auth review. Its loading-gate and missing-token redirect findings were accepted for repair. Its middleware rename suggestion was rejected because this project uses Next.js 16 proxy.ts, and its new-profile 404 suggestion was rejected because the backend already returns an incomplete profile. The authorized-party mismatch suggestion remains a configuration hypothesis.
