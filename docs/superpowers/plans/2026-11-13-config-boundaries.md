# Alignn configuration boundaries implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user's explicit execution method takes precedence: Claude Code CLI implements bounded contracts; Codex coordinates, reviews, tests and performs Git operations. Do not substitute native coding or a new agent relay.

**Goal:** Finish packet 1 of the approved organization design with a reviewed baseline map and a clean client/server configuration boundary, without duplicating PR #6 or changing runtime behavior.

**Architecture:** Extend the configuration implementation now merged into the hygiene branch. Browser-safe configuration has its own module; private environment access stays in a server-only module. Preserve the existing API origin helper, configuration truth table, auth guards and route behavior. Later state, folder and API work uses separate plans.

**Tech Stack:** Existing Next.js 16.4.5, React 19.3.1, TypeScript, Node 24, Playwright and installed TypeScript compiler. No new packages.

**Spec:** `docs/superpowers/specs/2026-11-13-codebase-organization-design.md`, approved by the user in this chat on 13 November 2026. It is committed on `codex/codebase-organization-design` and inherited by the planning branch. Codex must supply this spec and the approved plan to Claude as bounded context when implementation starts from the separate hygiene lineage; their absence from that lineage is not permission to skip them.

**Status:** Design approved. This implementation plan awaits the user's review before coding, as required by the selected writing-plans skill. No implementation or application tests have run for this plan.

## Global constraints

- "Keep Next.js/React/TypeScript, FastAPI/SQLAlchemy, PostgreSQL and Clerk. Keep authorization and business writes in FastAPI."
- "No single large rewrite."
- "Do not add a Clerk actor cache or legacy-auth fallback as a structural optimization."
- "Keep literal `NEXT_PUBLIC_*` accesses for Next.js inlining."
- "Never inspect, move, overwrite or publish existing environment/credential files."
- "No merges, closures, branch deletions, history rewrites or remote retargeting are authorized by this design approval."
- Preserve the modified README and untracked root handoff/handover and `docs/handover/`/`docs/tri-agent/` files; stage exact task paths only.
- Never modify the retained iCloud backup, existing runtime directories, real credentials, provider settings, infrastructure or deployment.
- Claude uses Read/Glob/Grep/Edit/Write only within the assigned source/tests/new documentation paths, with credentials/runtime/Git internals denied. No shell, agents, hooks, MCP servers or Git actions for Claude. Codex owns checks and focused commits.
- No dependency installs, upgrades, database changes or main-stack startup. Isolated application tests are not required for this configuration extraction; if later evidence requires them, use synthetic fixtures and deliberately isolated ports.

## Current baseline and branch decision

GitHub refreshed on 13 November 2026 after design approval:

- PR #6 **has merged into** `codex/version-control-hygiene`; merge SHA `0b95ee461d1293c73bab95803d5c113739236326`. Its central configuration code is already present there.
- PR #3 remains open, targeting `codex/audit-vercel-recovery`.
- PR #7 remains open at `5440d34`, targeting the hygiene branch. The readiness repair has not been merged by this chat.
- Documentation PR #8 remains a draft against the readiness branch. The earlier design inventory remains a dated snapshot; this update supersedes its statement that #6 is open.
- Planning branch: `codex/config-boundaries-plan`, based on documentation commit `8aad830`.

After plan approval, Codex creates `codex/web-config-boundaries` from fetched `origin/codex/version-control-hygiene` at `0b95ee4`, preserving dirty files. Recheck the remote head first; if it advanced, inspect the delta and record the resulting base. Do not silently merge or cherry-pick PR #7/#8 into it. Open the implementation PR against `codex/version-control-hygiene`, name dependency #3 and note #6 is already included. This extends the existing configuration work without modifying its historical branch or PR.

The session-readiness file from PR #7 does not exist on this implementation baseline. Its publishable-key import will be reconciled after its lineage is integrated through an explicit reviewed decision; this packet must not copy that draft into the configuration branch.

## File and ownership map

| Path                                             | Change / responsibility                                                                      |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| `docs/architecture/baseline.md`                  | New, compact branch dependency and source/verification checkpoint                            |
| `apps/web/src/lib/config/client.ts`              | New, only the browser-safe publishable-key presence export                                   |
| `apps/web/src/lib/config/server.ts`              | New, server-only presence/origin exports; imports public flag from client module             |
| `apps/web/src/lib/config.ts`                     | Remove after its consumers migrate; do not leave a compatibility barrel                      |
| `apps/web/src/app/layout.tsx`                    | Use explicit client-safe config path                                                         |
| `apps/web/src/proxy.ts`                          | Use explicit server-only config path                                                         |
| `apps/web/src/app/login/[[...login]]/page.tsx`   | Use explicit server-only config path                                                         |
| `apps/web/src/app/signup/[[...signup]]/page.tsx` | Use explicit server-only config path                                                         |
| `apps/web/src/app/onboarding/page.tsx`           | Use explicit server-only config path                                                         |
| `apps/web/src/app/workspace/page.tsx`            | Use explicit server-only config path                                                         |
| `apps/web/tests/config.spec.ts`                  | New, synthetic configuration truth-table and architectural boundary regressions              |
| `docs/architecture/configuration.md`             | New, configuration ownership, module rules, build/runtime limitations and deferred migration |

`next.config.ts`, `lib/api-origin.ts`, API settings, auth implementations, package manifests/lockfiles, existing browser tests and prior dirty documentation are read-only in this packet.

## Review focus

1. Missing either Clerk setting must retain the existing disabled/unconfigured guard; a presence check must not imply authentication. Test all four key-presence combinations in Task 2.
2. A browser consumer must not acquire private configuration through a convenient shared import. Pin the client module's literal public lookup, private-name absence, server marker and explicit consumer imports in Task 2.
3. Empty and unset PUBLIC_ORIGIN are different in the existing nullish fallback. Preserve both exactly and test explicit, missing and empty origins in Task 2. The existing localhost fallback is documented as a remaining deployment-policy concern, not newly endorsed as production-safe.
4. Tests must not read the developer's configuration or send synthetic authentication to a provider. Evaluate modules in an isolated VM using only test-owned environment values in Task 2; never load `.env*`.
5. Next.js must still compile server-only configuration from proxy and server pages. Run the real web build in Task 2; a simulated module test alone does not establish framework compatibility. Real Clerk login, production settings and account-switch behavior remain explicitly unverified.

## Task 1: Record the baseline and preserve branch ownership

**Owner:** Codex. Documentation and Git coordination only.

**Files:** Create `docs/architecture/baseline.md`. Read the approved spec, repository instructions and the current PR/ref metadata. Do not edit the dirty README or old handover files.

**Interfaces:** Consumes the baseline decision above. Produces a concise source checkpoint naming the coding branch/base, #3/#6/#7/#8 dependencies, retained dirty paths, current evidence limits and the fact that historical passing checks do not validate a new change.

- [ ] Recheck `git rev-parse --show-toplevel`, `git status --short`, GitHub #3/#6/#7 metadata and the fetched hygiene head. Expected: the active checkout is `/Users/abhigyandwivedi/Developer/alignn-web`; dirty paths remain preserved; inspect any changed heads before choosing the coding base.
- [ ] Create `codex/web-config-boundaries` at the verified hygiene head using an ordinary branch, without a worktree, merge, reset, clean or stash. Expected: existing dirty files carry intact; the new branch includes PR #6's configuration module.
- [ ] Write `docs/architecture/baseline.md` with the exact verified dependency map and the scope/evidence distinctions above. Expected: no credential values, access-bearing links, runtime data or assertions of deployment readiness.
- [ ] Run `node_modules/.bin/prettier --check docs/architecture/baseline.md`. Expected: exit 0; fix formatting only if needed.
- [ ] Stage only `docs/architecture/baseline.md` and commit `docs(architecture): record configuration refactor baseline`. Expected: existing staged formatter and redacted secret-scan hooks pass; unrelated dirty paths remain unstaged. No application test is warranted for this documentation-only task.

## Task 2: Split configuration and migrate existing consumers

**Owner:** Claude Code implements; Codex runs checks, reviews and commits.

**Interfaces:**

- `config/client.ts` exports `isClerkPublishableKeyConfigured: boolean`, derived only from the literal `process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` lookup. No private configuration imports or exports.
- `config/server.ts` starts with `import "server-only"`; exports `isClerkServerConfigured: boolean` from public-key presence plus `process.env.CLERK_SECRET_KEY` presence, and `publicOrigin: string` using the existing `process.env.PUBLIC_ORIGIN ?? "http://localhost:3000"` behavior. Never export private values. No runtime parsing or auth-policy change.
- `config.spec.ts` contains a test-only `evaluateConfig(environment: Record<string, string | undefined>): { client: { isClerkPublishableKeyConfigured: boolean }; server: { isClerkServerConfigured: boolean; publicOrigin: string } }` helper. It transpiles only the assigned config source modules with installed TypeScript, evaluates in a fresh Node VM with a test-owned `process.env`, and permits only the server-marker and client-module imports. Stub the marker only in that isolated test; normal production source keeps it intact. Do not add production APIs solely for testing.

- [ ] Claude writes the following behavioral/architecture tests first in `apps/web/tests/config.spec.ts`:
  - `public configuration follows publishable-key presence`: missing/empty value → false; a synthetic nonempty string → true. Assert only the public boolean is exported.
  - `server configuration requires both settings`: public/private presence truth table → false/false/false/true; private-only must not configure the client. Values are synthetic and must never be printed as configuration.
  - `origin preserves explicit missing and empty values`: `https://alignn.test` stays exact, missing uses `http://localhost:3000`, empty stays empty. This proves extraction compatibility rather than approving the existing origin policy.
  - `configuration respects client and server boundaries`: require literal public lookup, forbid private-name access/re-exports/imports in client config, require the server marker, and assert layout imports client config while proxy/login/signup/onboarding/workspace import server config. Import statements are inspected as an architecture contract, not inferred from substring coincidence in comments.
- [ ] Codex runs `npm exec --workspace @alignn/web -- playwright test tests/config.spec.ts --project=desktop --workers=1`. Expected initially: failure because the split modules do not exist, with no browser or app server launched. Record the failure; do not treat an unrelated fixture/config error as the intended red test.
- [ ] Claude creates `config/client.ts` and `config/server.ts` with the interfaces above and updates only the six listed consumer files. Preserve the guard expressions, Clerk options, props and page routing; this is an extraction, not a behavior change.
- [ ] Claude checks all imports of the old module, then removes `config.ts` once none remain. No compatibility barrel or parallel helper remains. Removal of this replaced module is within the user's explicit duplicate/dead-code cleanup authorization.
- [ ] Claude writes `docs/architecture/configuration.md`: public build-time vs private server variables; explicit module imports; origin validation already in `api-origin.ts`; existing missing-origin fallback limitation; API/web environment-file coupling and its deferred migration; PR #7 readiness integration still pending; commands and evidence boundaries. Include variable names only, no environment-file reads or examples copied from runtime.
- [ ] Codex runs the focused test command again. Expected: all config tests pass; no provider/database/network dependency and no skipped tests. Keep the final count as observed evidence, not a predetermined number.
- [ ] Codex runs `npm run lint:js`, `npm run lint`, `npm run typecheck` and `NEXT_TELEMETRY_DISABLED=1 CLERK_TELEMETRY_DISABLED=1 npm run build` from repo root, then Prettier checks on the two new architecture notes. Expected: exit 0 for each. Tools may consume existing configuration internally; never display environment values or copy `.env*` into reports. If build output contains sensitive diagnostics, keep them out of chat and report redacted error locations only.
- [ ] Codex reviews exact changed files and the original/new presence/guard semantics, then temporarily inverts the public-key presence decision, reruns the focused tests and confirms a behavioral failure. Restore from a local copy immediately, not a Git reset; rerun the focused test. Expected: mutation fails, restored implementation passes. No live credentials are touched.
- [ ] Codex stages only the new config modules, removed legacy config module, six consumers, config tests and `docs/architecture/configuration.md`; commits `refactor(web): separate public and server configuration`. Expected: hooks pass with no unrelated files staged.
- [ ] Codex publishes only the task branch and opens a scoped PR against the hygiene branch, naming #3 and the incorporated #6. Include actual checks, no-browser/no-auth verification limits, pending #7 integration, risks and revert instructions. No merge/retarget/delete action follows automatically.

## Claude implementation contract

Use Sonnet with medium effort for this extraction and tests, escalating effort only for a demonstrated framework boundary problem. Set a bounded per-pass spend cap, preserve the source-only credential/runtime exclusions, and use independent test-first and implementation passes so Codex can observe RED then GREEN. Claude cannot execute checks or Git; Codex returns their concise results for any required correction.

Claude's allowed edit paths are exactly the Task 2 source/test/new-documentation paths in the map. Explicitly exclude `README.md`, old handoffs, `.env*`, `.git`, `.claude`, `.superpowers`, `.next`, node_modules, private uploads and auth caches. The implementation report goes into a task-specific new note or chat result; do not overwrite the untracked `HANDOFF.md`.

## Remaining approved roadmap

After this packet, prepare separate plans for: shared transport/error/presentation helpers; saved/account state and closed-detail recovery; discovery ownership/URL/polling; the applications API/UI vertical slice with real PostgreSQL; onboarding validation/upload/state extraction; and proven cleanup plus contributor documentation. The approved design defines their acceptance criteria. No claim is made that this first packet fulfills the entire ten-item refactor.

## Self-review and completion contract

Spec coverage: packet 1 only, with all later packets explicitly retained. Module/export names and consumer paths match the existing PR #6 implementation. All five review-focus cases have a test/check owner in Task 2. No unnecessary package, behavior, provider, deployment or API change is introduced.

Complete this packet only after the exact source diff is reviewed, the intentional mutation is caught, restored tests/checks pass, source changes are committed separately from baseline docs and the PR describes current limitations. If a check cannot run, report the specific block and leave the corresponding acceptance item incomplete.

## Official framework references

- [Next.js environment variables](https://nextjs.org/docs/app/guides/environment-variables): public variables are inlined at build time; dynamic lookups are not inlined.
- [Next.js server/client boundaries](https://nextjs.org/docs/app/getting-started/server-and-client-components#preventing-environment-poisoning): the server-only marker rejects accidental Client Component imports; Next handles that marker internally without requiring a new package here.
