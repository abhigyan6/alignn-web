# Alignn

An opportunity and participation platform for students, teams and organizers.

Alignn brings together opportunity discovery, explainable eligibility, application tracking, team registration, submission rounds and organizer-reviewed results.

## Project status

The architecture and marketplace design direction were approved on 3 November 2026. The backend currently implements identity, jobs, profiles, organizations, discovery, external tracking, teams and registration. A working Next.js discovery interface now connects to the API, with authentication, account-link handling, opportunity details and saved opportunities. This is an implementation checkpoint, not a completed product.

The selected architecture is a Next.js web app, a FastAPI modular backend, a Python background worker and PostgreSQL. Resumes and submissions use private S3-compatible object storage.

## Project documents

- [Approved design](docs/superpowers/specs/2026-11-03-alignn-design.md)
- [Implementation plan](docs/superpowers/plans/2026-11-03-alignn-implementation.md)
- [Marketplace visual reference](docs/design/marketplace-concept.html)
- [Source project assessment](docs/source-assessment.md)

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

Use Node 24 and the Python environment installed from `apps/api/uv.lock`. Configure `.env` using `.env.example`, start PostgreSQL and apply migrations as described in `docs/runbooks/local-development.md`.

```sh
npm ci
apps/api/.venv/bin/alembic -c apps/api/alembic.ini upgrade head
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m uvicorn alignn.main:app --host 127.0.0.1 --port 8000 --reload
# In another terminal
NEXT_TELEMETRY_DISABLED=1 npm run dev
```

Open http://localhost:3000/explore. The frontend forwards `/api/*` to loopback port 8000, and PUBLIC_ORIGIN must be http://localhost:3000. The catalog intentionally stays empty until published records exist; concept fixtures are not live listings. Run the separate Python worker and local SMTP inbox for account email delivery.

Checks: `npm run lint`, `npm run typecheck`, `npm run build`, `npm run test:e2e` (requires running web/API and installed Google Chrome), and `apps/api/.venv/bin/python -m pytest apps/api/tests -q` with a migrated, dedicated TEST_DATABASE_URL.

Current checkpoint evidence: 53 API tests and 6 desktop/mobile browser tests passed locally. Browser tests cover discovery/category requests, invalid login and missing verification tokens; they do not establish a complete hosted-event lifecycle or production readiness. Follow-up work includes the full participant/profile/tracker workspace, organizer/admin interfaces, judging, reminders, privacy lifecycle, remaining revised abuse/trust rules and operational validation.

Manrope is served locally through @fontsource/manrope under SIL Open Font License 1.1 (copyright The Manrope Project Authors). The drawn loop mark is a proposed vector variation, not an exact reproduction of the supplied brand master.

 Production deployment, paid services and migration of existing users are outside the current repository setup.
