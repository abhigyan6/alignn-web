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

## Why this stack

These are engineering reasons for the existing choice, not benchmark results or a claim that this is the only suitable stack.

- **Next.js / React / TypeScript:** public opportunity pages and interactive discovery, profile and application screens can share components and types. A framework does not establish the visual design: tokens, layouts, content and interaction states still need deliberate implementation.
- **Python / FastAPI:** collection, normalization, profile matching and the API can share Python data models and libraries. Python also leaves a practical path for future document extraction, which is not implemented just because a resume can be uploaded. FastAPI supplies request validation and OpenAPI contracts.
- **PostgreSQL:** profiles, skills, saved opportunities, source identities and application history have relational constraints. Transactions and unique constraints support consistent writes and deduplication; existing full-text search and durable job leasing avoid introducing separate search/queue services before they are needed.
- **Clerk:** reuses the selected authentication provider rather than implementing password handling and recovery ourselves. Alignn's profile, onboarding state and authorization remain application responsibilities.
- **Separate Python worker:** long-running collection and file-processing work need not occupy an API request. The worker shares the backend code and PostgreSQL queue, preserving the modular-monolith architecture.

The tradeoff is running a JavaScript frontend plus Python API/worker processes, with contracts between them. This is more operational work than one server-rendered application. It is a reason to keep deployment simple, not evidence that another framework would fix UI consistency or collection quality. Hosting vendors can change without rewriting this stack.

## Competitor disclosures checked 12 November 2026

| Platform | Public evidence | Limit of the evidence |
|---|---|---|
| Unstop | Its own [October 2022 developer vacancy](https://unstop.com/jobs/software-developer-meanmernlamp-stack-developer-unstop-271195/amp) lists Angular, PHP Laravel, Node.js, MySQL 8, an unspecified NoSQL database and AWS services. | Historical disclosure, not a verified inventory of its current platform. The vacancy uses the imprecise wording "AngularJS 10"; no current Angular version is inferred. |
| Devfolio | Its [About page footer](https://devfolio.co/about/) credits Gatsby.js and Framer Motion. Its [backend engineering vacancy](https://devfolio.notion.site/Backend-Engineer-6266e2d8da6a4c12b8686ba759d4a528) names Node.js, Python, Go, Redis, MySQL and PostgreSQL. | The footer describes the marketing site. The undated vacancy is marked "Not actively hiring" and does not establish the complete current backend. |

No full current stack is asserted for Internshala, Hack2skill or other competitors without a reliable platform-owned disclosure. Jobs advertised by other employers on a platform, or courses it sells, do not establish that platform's implementation. Competitor choices are useful context; Alignn's product requirements and operating capacity should drive its own choices.
