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
