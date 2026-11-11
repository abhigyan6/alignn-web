# Local development

Use Python 3.12 or newer, uv, Node.js 24 and PostgreSQL 18. The API is started from the repository root.

```sh
cp .env.example .env
uv sync --project apps/api --locked
uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head
uv run --project apps/api uvicorn alignn.main:app --reload --host 127.0.0.1 --port 8000
```

Configure a separate `TEST_DATABASE_URL` whose database name includes `test`. Tests truncate this dedicated database; they refuse to proceed without that explicit setting.

```sh
DATABASE_URL="$TEST_DATABASE_URL" uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head
uv run --project apps/api pytest apps/api/tests -q
```

`infra/compose.yaml` provides PostgreSQL, a local mail inbox, private object storage and a scanner when Docker is available. Set `POSTGRES_PASSWORD`, `OBJECT_ACCESS_KEY` and `OBJECT_SECRET_KEY` before running `docker compose -f infra/compose.yaml up -d`. Create the `alignn_test` database separately. Compose storage volumes preserve local records. Development-only passwords in `.env.example` must never be reused for production.

On the initial development machine, PostgreSQL is installed with Homebrew and uses a separate project-local cluster under ignored `.superpowers/postgres`. It listens only on `127.0.0.1:55432`; no login service is registered. The database password is stored in the ignored `.env` and `.superpowers/database-password` files. Use the project interpreter at `apps/api/.venv/bin/python` if uv's shared cache is unavailable in a sandbox.

The API never creates tables on startup. Run Alembic explicitly before starting it. `/api/health` checks the process; `/api/ready` checks database/schema access. Interactive API docs are at `/docs` in development only.

## Active local checkout and Clerk (4 November 2026)

Use `/Users/abhigyandwivedi/Developer/alignn-web`, outside iCloud Drive. Do not start services from the retained Documents backup. Dependencies and build caches are installed in the new checkout. Its durable Python runtime is under `.superpowers/python` and its virtual environment is `apps/api/.venv`.

```sh
cd /Users/abhigyandwivedi/Developer/alignn-web
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m uvicorn alignn.main:app --host 127.0.0.1 --port 8000 --reload
# Another terminal, same checkout:
NEXT_TELEMETRY_DISABLED=1 CLERK_TELEMETRY_DISABLED=1 npm run dev
# Another terminal, same checkout, for jobs:
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m alignn.jobs.worker
```

Use `http://localhost:3000`, matching `PUBLIC_ORIGIN`. Next.js binds to `localhost`; using a different hostname caused the Clerk SDK's same-origin rewrite to proxy back into itself in this environment. API and PostgreSQL remain on loopback ports 8000 and 55432.

Clerk application: `app_3Le1eF6dgzjD83ZbHCzZ5sb5xMN` (Alignn), development instance. Keys were pulled using the official CLI into ignored `apps/web/.env.local`, mode 0600. Never print secrets or commit this file. The monorepo CLI may write `CLERK_PUBLISHABLE_KEY`; Next config maps that public value to `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` if the conventional name is empty. FastAPI's settings also load this private development env file. For deployment, configure Clerk secrets separately on the API and web hosts; deployment is not configured here.

`AUTH_PROVIDER=clerk` is the application default. Local passwords/sessions remain available only under explicitly selected `AUTH_PROVIDER=local`, used by legacy regression tests. With Clerk selected, legacy auth endpoints return 410 and old session cookies cannot authenticate. There is no automatic fallback to local auth when Clerk fails. A session bearer token is required by protected API operations; mutations also require exact Origin. Clerk verifies identity; PostgreSQL owns roles and permissions.

First use maps the verified Clerk subject to a stable local user UUID. Existing email collisions fail with `account_migration_required`; no local account is claimed by email alone. Existing passwords, profiles and records are retained. Existing-user import, password-hash migration and OAuth identity linking have not been implemented, so old accounts require a separate reviewed migration before public rollout. Clerk session revocation and deleted/banned users are checked on authenticated requests through Clerk's user API; this adds an external request. Account deletion does not yet purge local profile data; a deprovisioning/privacy workflow remains a launch requirement.

Start PostgreSQL from the new directory after a reboot:

```sh
/opt/homebrew/opt/postgresql@18/bin/pg_ctl -D .superpowers/postgres -l .superpowers/postgres.log -o '-p 55432 -h 127.0.0.1 -k /private/tmp -c max_connections=160' start
/opt/homebrew/opt/clamav/sbin/clamd --config-file=.superpowers/clamav/clamd.conf
/opt/homebrew/bin/mailpit --listen 127.0.0.1:8025 --smtp 127.0.0.1:1025 --database .superpowers/mailpit.db --disable-version-check --ignore-duplicate-ids
```

Run scanner and mail commands in separate terminals. These are local development services, not production hosting. The original database was cleanly stopped before copying; never run both clusters on the same port.

## Working without Docker or LocalStack (11 November checkpoint)

The existing native services are sufficient for current development: project PostgreSQL on 55432, FastAPI on 8000, Next.js on localhost:3000, ClamAV on 3310 and Mailpit SMTP on 1025. Keep the existing ignored runtime configuration; do not replace it with example credentials. Private development uploads use the existing local object adapter. No LocalStack, Colima, Kubernetes or additional monitoring service is required for this workflow.

Run the read-only check from the active repository:

```sh
python3 scripts/local-status.py
```

The script checks HTTP availability/readiness and TCP ports, not private data or credentials. A passing port check does not verify malware definitions or successful email delivery. The worker and scheduler need their own terminals:

```sh
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m alignn.jobs.worker
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m alignn.jobs.scheduler
```

Use one local worker and scheduler initially; avoid starting duplicates. These use the existing PostgreSQL queue and six-hour source schedule, not new infrastructure. The resumed local run recorded completed Devfolio, Greenhouse and Remotive ingestion jobs. This is local evidence only. Heroku/S3/AWS production state was not inspected or changed by this repair pass.
