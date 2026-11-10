# Heroku API and PostgreSQL deployment preparation

Superseded hosting placement: the latest user decision runs FastAPI on AWS alongside Next.js and the worker. Heroku provides PostgreSQL only. Follow `aws-hosting.md`; do not start a Heroku API dyno from this historical runbook.

Status: configuration prepared on 5 November 2026; not deployed. The latest user-approved hosting direction is Heroku for FastAPI and PostgreSQL, with Next.js and the Python worker/scheduler on AWS and private objects in S3. Clerk remains the identity provider. This supersedes the RDS placement in the earlier staging proposal; it does not change the modular-monolith architecture.

## Budget and limits

Heroku student credits apply at most $13/month for 24 months, with no monthly rollover. Basic web is listed at $7/month and Essential-0 PostgreSQL at $5/month: $12 recurring for these two resources, excluding one-off dynos, other products and taxes. Release-phase migrations consume dyno time. Do not add a continuously running Heroku worker within this estimate. Confirm the actual credit grant, billing cycle and current usage before provisioning; credit is not a spending cap.

Essential-0 has 1 GB storage and 20 connections. It is a constrained starting tier, not evidence that launch SLOs or recovery targets are met. Choose the region after checking available regions and latency to the AWS worker and the intended users. Verify provider PostgreSQL major-version availability before creating the database; local development currently uses PostgreSQL 18. No downgrade or data import is automatic.

## Prepared code

- Root `heroku.yml` builds only the API from `apps/api/Dockerfile` on a Cedar container app. The API image includes libmagic and locked Python dependencies. The Docker context is `apps/api`; root environment files and web credentials are excluded. No build requires application secrets.
- The release phase runs Alembic once. The web command binds to `$PORT` with one Uvicorn process. No development seed is run.
- Settings normalize Heroku's `postgres://` URL to the installed psycopg 3 SQLAlchemy driver, preserving credentials and query parameters.
- Connection pool settings are configurable per process. Set `DATABASE_POOL_SIZE=3`, `DATABASE_MAX_OVERFLOW=2`, `DATABASE_POOL_TIMEOUT=10` on the API, worker and scheduler: at most 15 combined connections, leaving five for migrations and maintenance. More processes require recalculating the budget before scaling.
- Set `API_ORIGIN=https://<actual-heroku-app-host>` in the Next.js **build** environment. Rebuild when it changes. Browser requests stay on the website's `/api/*` paths; Next forwards them over HTTPS. Clerk tokens retain the website's authorized origin. Do not put a database URL or secret key in a `NEXT_PUBLIC_*` setting.

## Required runtime configuration

Keep local `.env` files unchanged. Set production values separately on each host through authenticated secret configuration, without pasting them into chat, source control, build arguments or logs.

API: `ENVIRONMENT=production`, `AUTH_PROVIDER=clerk`, provider-managed `DATABASE_URL`, pool settings above, `PUBLIC_ORIGIN=https://<website-host>`, Clerk secret key, private object driver/bucket/endpoint/credentials, mail host/port/from and scanner configuration. Production validation remains enabled; placeholders must not bypass it.

Enforce database TLS with libpq configuration such as `PGSSLMODE=require` on **every** database process, including release migrations. Before public launch configure certificate verification (`verify-full`) using the provider's documented CA chain and verify it succeeds from both hosts. Never print `heroku config`, full database URLs or connection exception locals.

Worker and scheduler: same database and production settings as the API, with their process-specific pool limits. Run one of each, from the same source revision as the API. ClamAV stays alongside the worker, reachable privately; do not expose unauthenticated port 3310 to the Internet. Private API-to-storage credential delivery and worker instance-role support remain unresolved. Current S3 settings require explicit credentials, so role-only deployment is not ready yet. SMTP transport and scanner readiness also require verification.

Next.js: production Clerk keys, exact website origin configured in Clerk, server-side `API_ORIGIN` at build time, HTTPS reverse proxy, and private cache behavior. Verify authenticated API calls through the deployed proxy rather than testing only the direct Heroku URL.

## Provisioning and release gates

1. Authenticate Heroku, verify the intended personal account and actual student credit entitlement. Choose an available region and app name; do not select paid third-party add-ons.
2. Create a Cedar container app, provision exactly Essential-0, and select one Basic web dyno. Confirm price and resource inventory. Do not also run the previous RDS proposal by accident.
3. Configure runtime secrets, TLS and host networking. Pin the source revision for all processes. Build the image and verify dependency installation, migrations, health/readiness and production startup checks.
4. Back up any source data before an explicit import. Rehearse database restore and verify row counts/ownership. Merely changing `DATABASE_URL` does not migrate data. Define backup frequency and recovery targets from available provider capabilities; no 15-minute RPO or four-hour RTO is claimed here.
5. Run live sign-in/onboarding, discovery, saved opportunities, matching/ingestion and quarantined upload/scan/download tests through the HTTPS website. Check latency, pool usage and API memory within the Basic dyno's 512 MB limit.
6. Monitor billing, failed jobs and storage growth. A database rollback after writes requires a reconciled data plan. Remove the old RDS instance only after a separately authorized backup/cleanup action and successful verification; it can continue incurring costs until cleaned up.

## Verification evidence

Local checks: 75 PostgreSQL-backed API tests passed; Ruff passed on changed Python files; web TypeScript and formatting checks passed. Container build, Heroku release, provider TLS, cross-cloud latency, memory/load envelope and restore are unverified. Docker and the Heroku CLI were not installed on PATH during initial inspection.

## Official references

- [Student credit rules](https://help.heroku.com/Z3RHNRHD/how-does-the-heroku-for-github-students-program-work)
- [Current pricing](https://www.heroku.com/pricing/)
- [PostgreSQL connections and TLS](https://devcenter.heroku.com/articles/connecting-heroku-postgres)
- [Container build and release manifest](https://devcenter.heroku.com/articles/build-docker-images-heroku-yml)
