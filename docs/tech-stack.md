# Alignn tech stack

Repository snapshot: 11 November 2026. This describes the codebase and agreed deployment target; it is not a claim that every production service is deployed.

## Short version to forward

Alignn is an India-first career opportunity discovery platform built with Next.js, React and TypeScript on the frontend, and Python/FastAPI on the backend. It uses PostgreSQL with SQLAlchemy and Alembic, Clerk for authentication, and a separate Python worker with a PostgreSQL-backed job queue. A standalone Python scraper collects public opportunity data through GitHub Actions; the backend validates and imports it automatically. Search uses PostgreSQL full-text search, and profile matching uses transparent Python scoring. The planned production setup is AWS application hosting, Heroku PostgreSQL and private S3 file storage. Development and testing currently run locally.

## Components

| Area | Technology / purpose |
|---|---|
| Web | Next.js16.4.5, React19.3.1, TypeScript; custom CSS tokens/components and Manrope typography. |
| API | Python3.12+, FastAPI, Uvicorn and Pydantic validation; modular monolith. Business writes and authorization stay here. |
| Database | PostgreSQL, SQLAlchemy2, psycopg3; Alembic migrations. PostgreSQL full-text search with a GIN index. |
| Authentication | Clerk integration in Next.js and backend session/token validation. |
| Jobs | Separate Python worker processes and scheduler; PostgreSQL durable queue, leases, retry cap and maintenance/collection lanes. |
| Collection | Independent `alignn_scraper` package: HTTPX, standard-library HTML/JSON parsers, robots/host/time/size bounds; private GitHub Actions manual trigger and gated cron. Legacy local Devfolio adapter also uses Scrapy. |
| Data delivery | Private JSON chunk/manifest bundle; pinned GitHub run/artifact identity, digest/schema validation, source receipts, automatic worker import and expiry checks. |
| Matching | Python profile/skill/project fit scoring; PostgreSQL match snapshots. No hosted LLM is required by the current scoring implementation. |
| Files | Private object-storage adapter for S3 via boto3; local filesystem in development. ClamAV scanning worker integration. |
| Email | SMTP adapter; Mailpit for local development. Production provider/configuration needs separate verification. |
| Testing | pytest with real PostgreSQL integration tests; Playwright browser test tooling; Ruff and TypeScript/format checks. |
| Deployment target | AWS application hosting + Heroku PostgreSQL + private S3 files, as agreed. Production activation is pending; this scraper change did not deploy infrastructure. |

The private collector is [abhigyan6/alignn-scraper](https://github.com/abhigyan6/alignn-scraper). Operational setup and remaining activation steps are in [the scraper runbook](runbooks/india-scraper.md).
