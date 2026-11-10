# Alignn

A career opportunity discovery platform for students.

Alignn centers on profile-based opportunity discovery, explainable eligibility and application tracking. Source-specific collection and resume parsing are still pending. Hosted events are a secondary workflow.

## Project status

The architecture and marketplace design direction were approved on 3 November 2026. The backend currently implements identity, jobs, profiles, organizations, discovery, and external application tracking. Alignn discovers events and links to their original organizers. Event hosting, teams and registration inside Alignn have been retired. A working Next.js discovery interface now connects to the API, with authentication, account-link handling, opportunity details and saved opportunities. This is an implementation checkpoint, not a completed product.

The selected architecture is a Next.js web app, a FastAPI modular backend, a Python background worker and PostgreSQL. Resumes and submissions use private S3-compatible object storage.

## Project documents

- [Approved design](docs/superpowers/specs/2026-11-03-alignn-design.md)
- [Implementation plan](docs/superpowers/plans/2026-11-03-alignn-implementation.md)
- [Marketplace visual reference](docs/design/marketplace-concept.html)
- [Source project assessment](docs/source-assessment.md)

The hosting retirement keeps the historical database tables and records. The scheduler removes expired request replay rows and clears academic evidence from retired events after 180 days by default, measured from the later of event end and evidence creation. Set `RETIRED_EVENT_EVIDENCE_RETENTION_DAYS` to override the default. Run the latest migration before restarting the API and web together. Existing profiles with a degree and graduation year keep their workspace access. New profiles require explicit onboarding completion, and the private resume upload remains optional.

The visual reference contains illustrative content and does not accept real registrations. The original repository, `Vaidik04/Alignn`, was inspected for workflow context. This is a fresh repository with independent history.

## Intended application layout

```text
apps/web                 Next.js web application
apps/api                 FastAPI application, migrations and Python worker
packages/api-client      Generated TypeScript API contract and client
packages/design-tokens   Shared semantic design tokens
infra                    Local services, proxy and deployment configuration
docs                     Specification, plan and operating instructions
```

## Run locally

Deployment preparation for the proposed Heroku API/database and AWS web/worker split is documented in [the staging runbook](docs/runbooks/heroku-staging.md). This configuration is not yet deployed.

Use Node 24 and the Python environment installed from `apps/api/uv.lock`. Configure `.env` using `.env.example`, start PostgreSQL and apply migrations as described in `docs/runbooks/local-development.md`.

```sh
npm ci
apps/api/.venv/bin/alembic -c apps/api/alembic.ini upgrade head
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m uvicorn alignn.main:app --host 127.0.0.1 --port 8000 --reload
# In another terminal
NEXT_TELEMETRY_DISABLED=1 npm run dev
```

Open http://localhost:3000/explore. The frontend forwards `/api/*` to loopback port 8000, and PUBLIC_ORIGIN must be http://localhost:3000. The catalog intentionally stays empty until published records exist; concept fixtures are not live listings. Clerk handles sign-in, verification and account recovery. Configure its development keys in `apps/web/.env.local`; see the local runbook. The separate Python worker handles matching and private-file scanning.

Checks: `npm run lint`, `npm run typecheck`, `npm run build`, `npm run test:e2e` (requires running web/API and installed Google Chrome), and `apps/api/.venv/bin/python -m pytest apps/api/tests -q` with a migrated, dedicated TEST_DATABASE_URL.

Current checkpoint evidence (4 November 2026): 66 PostgreSQL-backed API tests, 8 desktop/mobile browser tests, lint, production build and migration-drift checks passed from the non-iCloud checkout. Browser checks cover discovery, Clerk sign-in rendering, workspace protection and recovery redirects. They do not verify a real user's completed Google/email sign-in or the full authenticated onboarding journey.

Active checkout on the development Mac: `/Users/abhigyandwivedi/Developer/alignn-web`. The former Documents checkout is retained as a backup. See [migration checkpoint](docs/implementation/2026-11-04-clerk-and-local-migration.md) for the remaining iCloud file-recovery limitation.

Follow-up work includes source ingestion, resume parsing, the full personalized dashboard/tracker, organizer/admin interfaces, judging, reminders, privacy lifecycle and operational validation.

Manrope is served locally through @fontsource/manrope under SIL Open Font License 1.1 (copyright The Manrope Project Authors). The drawn loop mark is a proposed vector variation, not an exact reproduction of the supplied brand master.

 Production deployment, paid services and migration of existing users are outside the current repository setup.
