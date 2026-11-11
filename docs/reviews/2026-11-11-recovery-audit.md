# Alignn recovery audit

Reviewed current main at `1f10308` on 11 November 2026. Changes are on `codex/audit-vercel-recovery`. The coming-soon homepage is preserved.

## Fixed in source

- Vercel builds previously defaulted API rewrites and server profile requests to localhost. Centralized origin validation now disables rewrites when Vercel has no backend configured and rejects local/insecure Vercel backend origins. Account profile reads fail explicitly when the backend is missing.
- Server profile requests now have a ten-second timeout. A shared page error boundary offers retry and navigation home.
- Authenticated visits to login/signup now redirect on the server before displaying the auth card. Actual signed-in redirect flicker is still unverified.
- The homepage previously depended on Clerk initialization through SessionBridge. It now renders immediately, and its main landmark matches the skip link.
- Database defaults previously allowed 112 connections per process. Defaults now match the existing host settings of three pooled plus two overflow connections per process. Operators must still budget all processes and overrides.
- Removed unreachable JSX after the auth handoff redirect.

## Verified

- Full backend suite passed against a newly initialized PostgreSQL 18 database, 81 tests. Reviewed coverage includes identity, object ownership, organization verification, upload handling, external opportunity ingestion, job handling, and retirement of event hosting.
- Backend lint passed. After the pool default change, all 18 unit tests passed again.
- Frontend production build, type checking and formatting passed.
- Ten signed-out desktop/mobile browser checks passed for login, protected workspace/onboarding/edit routes and legacy recovery routing.
- API origin checks exercised local defaults, unconfigured Vercel, valid HTTPS and rejected origin inputs.
- npm production dependency audit and pip-audit of the installed Python environment reported no known vulnerabilities at audit time.
- A separate Vercel build with API_ORIGIN unset passed.

## Outstanding evidence and deployment blockers

- Browser tests still logged a Clerk session-refresh infinite-loop warning. This is evidence of an unresolved authentication/configuration issue. Signed-out checks do not verify successful login or new/returning-account onboarding. Credentials were not inspected.
- User reports AWS was shut down. This audit does not establish its current resource state or restart it. Vercel needs a reachable FastAPI backend, and its API_ORIGIN and exact PUBLIC_ORIGIN configuration must agree with the actual deployment.
- Vercel project inspection found Node 26 although repository engines require Node 24. Updated the project setting and verified Node 24 through a second project inspection. Local CLI inspection also created an ignored .vercel project link.
- Antigravity was requested for independent review. Its first headless attempt was denied command permission. A second source-only review timed out after three minutes without findings, so independent review is incomplete.
- Live signed-in journeys, private file scanning, ingestion scheduling, hosted resource state, external-service configuration and full production recovery remain unverified. No claim of complete application readiness or comprehensive security assurance is made.

See `docs/runbooks/vercel-frontend.md` for frontend/backend configuration steps.
