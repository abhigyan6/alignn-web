# Alignn repository organization and refactor design

13 November 2026. Status: **proposed; awaiting design approval**. The user selected feature-by-feature cleanup, with Codex coordinating/reviewing and Claude Code CLI performing bounded implementation. Superpowers planning is explicitly requested. This document does not claim implementation, tests, merges or deployment.

## Intent and scope

Make the existing application easier to understand and extend while preserving its behavior and the confirmed student journey: public discovery → Clerk → onboarding → recommendations → saves → external application → manual tracking. Keep Next.js/React/TypeScript, FastAPI/SQLAlchemy, PostgreSQL and Clerk. Keep authorization and business writes in FastAPI.

The ten requested outcomes are clean folders, UI/business separation, duplicate/dead-code removal, consistent names, error handling, configuration isolation, reusable components, state management, documentation and a scalable API structure. These form a sequence of independently reviewable changes; no single large rewrite.

Non-goals: redesigning screens; restoring event hosting; changing authentication providers; extracting resumes; replacing the database; introducing microservices; upgrading dependencies; activating pending CI/deployment designs; provisioning infrastructure or deploying. Scalability here means maintainable module boundaries and explicit contracts, not a measured throughput improvement.

## Approaches and selected direction

The user chose incremental feature-by-feature cleanup over a folders-first move. The former addresses ownership and behavior together and permits targeted regression checks. A folders-first move offers faster visual tidiness but creates widespread import churn before improving state and errors. A clean-slate rewrite conflicts with the instruction to preserve existing work and is excluded.

Codex's proposed implementation choices are dependency-free state management initially, feature folders inside the existing web application, and continued use of the existing backend domains. These choices are part of this proposed design, not prior user approvals.

## Verified checkpoint and branch inventory

Local checkout: `/Users/abhigyandwivedi/Developer/alignn-web`, branch `codex/session-readiness-repair`, commit `5440d34`. Preserve modified `README.md` and untracked `HANDOFF.md`, `handover.md`, `docs/handover/` and `docs/tri-agent/` exactly unless an individual document update is explicitly included in a later packet. The dated handover predates committed PR #6/#7 and must not be treated as current verification.

GitHub branch search was paginated to completion: 12 remote branches. Comparisons below were read from GitHub against `main` at `1f103087`; local `main` is older. Counts reflect commit ancestry, not whether every change is useful or correct.

| Remote branch                    | Ahead / behind main | Disposition proposed                                                                                            |
| -------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------- |
| `main`                           | 0 / 0               | Integration branch; never push directly                                                                         |
| `codex/audit-vercel-recovery`    | 19 / 0              | Review existing product/repair baseline; PR #2 is closed without merge, so it is not an active integration path |
| `codex/version-control-hygiene`  | 23 / 0              | PR #3 depends on the recovery baseline                                                                          |
| `codex/session-readiness-repair` | 24 / 0              | PR #7 depends on #3; current checkout                                                                           |
| `codex/web-env-config`           | 24 / 0              | PR #6 depends on #3; sibling of #7                                                                              |
| `codex/ci-pipeline`              | 25 / 0              | Draft #4, based on #3; design only                                                                              |
| `codex/deployment-pipeline`      | 27 / 0              | Draft #5, based on #4; design only                                                                              |
| `audit-vercel-recovery`          | 4 / 0               | Separate recovery history; inspect unique changes before choosing disposition                                   |
| `claude/kind-thompson-sg08qs`    | 2 / 0               | Separate marketing direction; do not merge merely to reduce branches                                            |
| `claude/nifty-volta-cw0ppo`      | 2 / 0               | Skill/documentation work; separate from app refactor                                                            |
| `build-alignn`                   | 0 / 2               | No unique commits against main; cleanup candidate                                                               |
| `main-backup-before-coming-soon` | 0 / 1               | No unique commits against main; retained backup candidate                                                       |

Local-only refs also matter: `codex/audit-vercel-recovery` has research commit `54329d1` ahead of its remote. `codex/agent-handover` and `codex/app-repair-baseline` point at `e310c4f`. Local `codex/build-alignn` differs from the similarly named remote `build-alignn`. None may be discarded by matching names alone.

Branch policy: keep a documented dependency map, one `codex/<task>` branch per packet and focused Conventional Commits. Open stacked PRs against their actual parent and name dependencies. Validate the recovery baseline before integrating its descendants. PR #6/#7 need review and a coordinated integration point, not silent cherry-picks or duplicated implementations. Leave #4/#5 separate. No merges, closures, branch deletions, history rewrites or remote retargeting are authorized by this design approval; provide an exact disposition proposal first. Local planning documents can be added on a dedicated task branch without changing existing application content.

## Source observations motivating the change

- Existing monorepo boundaries (`apps/web`, `apps/api`, `packages/api-client`) and backend domain folders are useful and should remain.
- `components/onboarding.tsx` is 773 lines, mixing option catalogs, validation, upload orchestration, network state and rendering.
- `components/application-tracker.tsx` is 429 lines, with handwritten response shapes, application/history loading, mutations, filtering and row UI.
- `components/workspace.tsx` is 326 lines. Account and shortlist requests refresh on local retry/tab dependencies rather than the session key. The application tracker likewise loads by retry counter. These are account-change risks to test, not verified browser leaks.
- `app/explore/page.tsx` is 388 lines and mixes URL filters, query construction, rank polling, request cancellation and screen rendering.
- Opportunity date formatting is duplicated in the application tracker. `isClosed`, date formatting and source labels are exported from a client card component and imported by other screens; domain/display helpers should not require a UI import.
- `lib/api.ts` is a useful single browser transport. It discards structured error codes, field details and request IDs, and returns `response.json()` without a normalized successful-response parse error. Keep a single transport while improving this boundary.
- `domains/applications/router.py` contains request schemas, SQL queries, creation/update rules and serialization. It lacks explicit output models; the web tracker consequently maintains handwritten response types. Other domains already demonstrate `schemas.py`/`service.py` patterns.
- `main.py` already handles domain errors, validation, conflicts, unexpected failures, transactions and request IDs. Extend/test this policy where needed rather than wrapping every function in blanket catches.
- The detail effect depends on listing ID/retry rather than identity readiness. `visible()` permits a CLOSED record only to an authorized actor; an initial anonymous read can therefore 404 before Clerk is ready without automatic recovery. This is a source-supported timing risk, not a reproduced browser result; add a cold-load regression while keeping public browsing immediate.
- Backend `Settings` currently reads both root configuration and the web local environment file. Separate ownership must be staged without breaking existing runtime configuration or inspecting its values.
- Team/participation models are retained by model registration, migrations, retention jobs and tests. They are **not proven dead code** and must remain.

## Target web structure and dependency rules

```text
apps/web/src/
  app/                         Next.js routes, layouts, route boundaries
  features/
    opportunities/             discovery/detail screens, cards, queries, rules
      components/
      hooks/
      api.ts
      types.ts
      opportunity-rules.ts
    saved/                     account-scoped saved reads and mutations
      hooks/
      api.ts
    applications/              tracker, row, history and mutation behavior
      components/
      hooks/
      api.ts
      types.ts
    onboarding/                form model/validation, steps and resume workflow
      components/
      hooks/
      api.ts
    account/                   workspace shell and account loading
  components/                  actually shared navigation, brand, loading, legal UI
  lib/
    api/                       browser transport, normalized errors, contract types
    auth/                      session bridge/readiness and server account access
    config/                    client-safe and server-only configuration
    format/                    shared India date presentation
```

Create folders only as a packet creates a real owner; do not scaffold empty layers. Screens become thin consumers of feature hooks and components. Pure formatting/rules can be imported without React or browser state. Reuse generated API schemas; feature types may describe local view state, not duplicate server contracts. Cross-feature consumers use explicit exported modules; do not add broad barrel exports that blur client/server boundaries. Keep existing style tokens and colocate feature styles when moving their owner.

Conventions: kebab-case web file/folder names, PascalCase React components/types, camelCase functions/variables and `use...` hooks. Python stays snake_case with descriptive domain verbs. Existing public URLs, database names and externally consumed API names remain compatible; rename internal symbols only with all callers/tests updated.

## State management and business logic

Separate server data, URL state and transient UI state. Discovery filters/search belong in the URL, with unsent input drafts local. Form drafts, open rows and notices stay local; use a reducer when transitions become coupled. Do not install Redux/Zustand/query libraries without demonstrated need and a separate dependency review.

Keep authentication verification and remote revocation checks intact. Do not add a Clerk actor cache or legacy-auth fallback as a structural optimization. Private server data must be keyed by current identity, hidden immediately when identity changes, and read only after session readiness. Abort obsolete requests and also prevent late mutation results from applying to another identity. A reusable saved-data owner must keep IDs, cards and mutations consistent across Home, discovery, details and workspace; choose a focused context/store only if its lifecycle improves on hook-local ownership. Avoid a global store containing unrelated profile, discovery and form state.

Keep useful public cards during ranking refresh. Pending, ready, failed/unknown and empty are distinct states; a failed saved read must not assert that nothing is saved. Expired session and access denial must retain their intended authentication behavior. Extract orchestration from UI without duplicating FastAPI eligibility, authorization or matching rules in the browser.

## Errors and environment configuration

Transport errors retain status plus optional API code, request ID and field errors. Network failure, readiness timeout, malformed response and abort have explicit handling; abort is not displayed as a failure. Messages shown to students are safe and actionable. Never log bearer tokens, private notes, resumes or raw response payloads. Read retries are user initiated or explicitly bounded. Do not automatically retry writes.

Each feature renders loading/error/retry/empty states and clears stale errors after recovery. Preserve Next.js route error recovery, accessible announcements and keyboard focus. Reconcile this with existing error handling instead of replacing working paths wholesale. “Everywhere” is verified through a maintained feature/error matrix, not a claim that every possible failure has been tested.

Review/reuse PR #6 as the configuration starting point. Split client-safe literals/flags from server-only configuration so browser modules cannot import server concerns. Keep literal `NEXT_PUBLIC_*` accesses for Next.js inlining. Keep origin validation and avoid silently replacing missing production settings with local defaults. Backend settings already belong in `alignn/config.py`; adapters consume validated settings. Document API-owned and web-owned variable names and test settings with synthetic values. Decouple the backend from the web environment-file fallback only through an explicit migration path that preserves existing startup; do not remove the fallback silently or move credential values. Runtime values remain externally supplied; never inspect, move, overwrite or publish existing environment/credential files. Add credential-free setup documentation and variable names only.

## Backend API structure

Retain `domains/<domain>/{models,schemas,service,router}.py`. Routers validate HTTP inputs and resolve actor/database dependencies; services perform ownership-scoped queries and business operations; schemas define explicit request/response contracts. Preserve request-owned transactions, row locks and database constraints. Services must not independently commit.

Start with applications, where the boundary is clearly missing. Preserve endpoints, status codes, CSRF and ownership checks. Explicit response models must retain the current data shape; regenerate OpenAPI/TypeScript through the existing exporter and review the diff. Then inspect profiles and opportunity operations in separate packets. Do not introduce generic repository wrappers, new ORM layers, pagination redesign, database migrations or renamed endpoints merely for symmetry. If pagination or API behavior needs changing, design and test that behavior explicitly as a separate packet.

## Delivery sequence and acceptance

| Packet                                       | Requested outcomes                                 | Acceptance evidence                                                                                                                                                              |
| -------------------------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Baseline and configuration                | Branch clarity; configuration; documentation       | Review PR #6/#7 and baseline dependencies; reconcile current checkout; configuration presence/missing-mode tests; no credentials inspected                                       |
| 2. Shared transport and presentation helpers | Errors; duplication; reusable modules; naming      | Preserve abort/auth/204 behavior; tests for HTTP/network/malformed payload handling and helper behavior; existing browser flows remain usable                                    |
| 3. Saved/account state                       | State management; UI separation                    | Session readiness, identity switch, stale read/mutation, retry, signed-out flow, cold-load closed-detail recovery and cross-screen save consistency regressions                  |
| 4. Discovery feature                         | Folders; hooks; reusable UI                        | URL back/forward and filters, pagination, bounded matching polling, retained public cards, failure/recovery and narrow-screen regressions                                        |
| 5. Applications vertical slice               | Scalable API; generated types; tracker modules     | Preserve creation/history/ownership/CSRF/status behavior with real PostgreSQL; generated response types; UI update/filter/history/error regressions                              |
| 6. Onboarding feature                        | Business/UI separation; form state; reusable steps | Preserve validation, focus, partial-save recovery, optional upload/scanning semantics and completion routing; no parsing claim                                                   |
| 7. Proven cleanup and contributor docs       | Dead code; names; documentation                    | Remove only proven-unused symbols/duplicate implementations; check dynamic/framework/worker/migration/test consumers; import/build checks and architecture/error matrix complete |

The first implementation contract is bounded to packet 1 review/integration decisions and a standalone configuration correction if needed; it is not permission to merge existing PRs. Each later packet uses its own spec/plan/Claude file allowlist and final Codex review. Sonnet is the default for bounded extraction; use stronger effort/models only when a particular cross-cutting problem warrants it. Claude receives source/test/docs access only, with no credentials, Git operations, shell or cloud access for ordinary coding passes. Codex runs relevant checks and reports actual outcomes.

For web changes use installed ESLint, Prettier, typecheck and build, plus focused behavioral regressions in Brave/in-app browser. Do not install dependencies reflexively or start the main app stack silently. Isolated proof servers require deliberate ports and cleanup. Backend changes require the dedicated migrated PostgreSQL test database; fixtures truncate that test database, so verify its identity internally before execution. No SQLite substitute. Add tests for behavior and regressions rather than implementation mirrors.

## Completion and evidence limits

The overall refactor is complete when all ten outcomes are evidenced by code boundaries, regression checks, updated contributor docs and reviewed focused PRs. Keep a migration/ownership map so later features have an obvious home. Remove temporary compatibility modules once their callers are migrated and proven unused.

No application code, services, tests, integrations, remote branches, PRs or deployments were changed by the audit/design phase. A local `codex/codebase-organization-design` branch was created from `5440d34` to hold only the proposed design; existing dirty files were retained. GitHub PR descriptions report prior passing checks for #6/#7; those are author-reported historical evidence, not independent checks by this chat. Source observations do not establish authenticated or deployed behavior. Remaining launch/security/product backlog stays visible and outside this structural refactor.

## Source links

GitHub metadata was checked directly through the connected GitHub tools on 13 November 2026: [repository](https://github.com/abhigyan6/alignn-web), [hygiene PR #3](https://github.com/abhigyan6/alignn-web/pull/3), [CI design #4](https://github.com/abhigyan6/alignn-web/pull/4), [deployment design #5](https://github.com/abhigyan6/alignn-web/pull/5), [configuration PR #6](https://github.com/abhigyan6/alignn-web/pull/6), [session repair PR #7](https://github.com/abhigyan6/alignn-web/pull/7). Branch-ancestry comparisons are point-in-time observations.

## Independent audit and design review

Claude Code completed a source-only Sonnet/high audit with Read/Glob/Grep tools, restricted file access, no shell, writes, MCP servers or credential-file reads. Its report was checked by Codex against relevant callers. Audit cost reported by that run: $1.0821488; this is not a total account bill. No checks ran. A fresh design reviewer found no important unanswered planning questions.

Codex did not adopt every audit suggestion: routers are needed only for HTTP-exposed domains, client-side validation/display remains useful UX rather than competing authorization, and remote identity verification must not be cached away. The homepage already has a catch handler, contrary to one audit sentence. No missing-document claim is made from a limited search. Potentially redundant endpoints, alternate ingestion paths and historical models remain candidates for later decisions, not automatic deletion.
