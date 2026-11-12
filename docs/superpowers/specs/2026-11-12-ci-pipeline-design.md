# Pull-request and main CI design

12 November 2026. Short design for approval under the user-selected Superpowers workflow. The existing CI workflow has not yet been replaced. This task uses its own codex/ci-pipeline branch/PR, stacked on the Git-hygiene PR until that dependency is merged.

## Goal and chosen approach

Run GitHub Actions for every pull request and every push to main, with cached installation, lint, typecheck, unit tests, real-PostgreSQL integration tests and a production build, in that order. One sequential job is the appropriate implementation here: it stops at the first failed step and avoids spending build time after an earlier gate fails. Independent parallel API/web jobs were considered but would not enforce the requested global order or global fail-fast behavior. No additional CI service is proposed.

Use ubuntu-24.04 with a 10-minute job timeout and cancellation of obsolete runs per PR/ref. Under ten minutes is a target to verify from actual Actions timings, not a measured result or a guarantee about GitHub queue time. If uncached runs exceed the budget, report and optimize the slow stage; do not skip tests or mark a timeout successful.

## Files and behavior

Replace .github/workflows/ci.yml, preserve workflow_call compatibility for existing deployment consumers, and add a workflow status badge to README.md. Add only narrowly necessary package scripts/configuration and workflow-contract tests; do not rewrite application code or databases to force CI green.

1. Checkout with read-only contents permission, no persisted checkout credential and full history for secret scanning. Pull-request code runs on GitHub-hosted ephemeral runners without repository/provider production secrets or OIDC deployment permissions. Never use pull_request_target to execute head code.
2. Install Node24 and Python3.12 with locked npm/uv dependencies. Cache npm's download cache using package-lock.json and uv's cache using apps/api/uv.lock, not node_modules or database state. Pin third-party actions to reviewed commit SHAs. Use the existing supported Node/TypeScript/Ruff toolchain; no browser downloads are needed for this requested API/unit/build pipeline.
3. Provision a real PostgreSQL18 service container with a health check and dedicated alignn_test database. Use an ephemeral test-only password, AUTH_PROVIDER=local and ENVIRONMENT=test; do not reuse production URLs. Install libmagic where required. Apply Alembic upgrade head during setup so shared autouse DB fixtures can run for both unit and integration suites.
4. Lint with the hygiene PR's JavaScript/TypeScript correctness rules, the repository's existing web formatting check and Ruff configured explicitly from apps/api/pyproject.toml. Run a redacted Gitleaks check with a reviewed pinned release/checksum. No blanket scanner allowlists or disabled checks.
5. Generate Next route types with next typegen before npm run typecheck, so a fresh checkout does not depend on a previous build's .next cache.
6. Unit tests: pytest apps/api/tests/unit, followed by the disposable Git-hook regression test. Integration tests: pytest apps/api/tests/integration, against the migrated service container. Separate commands make failures attributable. Both use the locked project interpreter and the existing dedicated-test-database safety guard. Do not substitute SQLite or mock SQL persistence.
7. Build with npm run build, no real Clerk secret/publishable key and telemetry disabled. This validates the production compiler; it is not a deployment or proof of authenticated browser acceptance.

Give steps clear names. Do not add continue-on-error, success fallbacks or retries that hide deterministic failures. Failure-only test reports may be retained seven days; no private env files, credentials, database contents or unredacted scanner reports are uploaded. Branch-protection required checks can be enabled after the actual new check name is green; this design does not silently configure or claim those protections.

## Acceptance and verification

- Workflow syntax/action references validate; PR and main triggers are present, other branch pushes do not duplicate PR runs, and workflow_call remains supported.
- Automated workflow-contract tests assert stage order, real PostgreSQL health setup, cache lockfile keys, read-only permissions, 10-minute timeout and absence of ignored failures.
- Deliberate bad-lint, type-error, failing-unit and failing-integration fixture branches fail at their own stage and never reach build. A migration failure stops setup and all later stages. Use temporary fixture branches, not edits committed into the application.
- A normal PR run passes every stage; record actual elapsed time and cache hit/miss results. Existing app tests may reveal genuine failures; fix within the appropriate reviewed task rather than weaken assertions.
- The README badge links to .github/workflows/ci.yml with branch=main. Do not fabricate a green status before main has run the updated workflow.

No deployment/production credential access, new cloud resources, history rewrite or direct main push is part of CI implementation. The initial hygiene history scan is documented separately. Next step after design approval: write the implementation plan with exact commands/tests, then execute through a reviewed PR.
