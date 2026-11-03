# Alignn project assessment

Reviewed 3 November 2026. Reference: Vaidik04/Alignn, main commit `021664d0dbe5a266e9abb451598931bed3877132`.

This is a source inspection and an architecture recommendation for the fresh `alignn-web` repository. It is not an approved implementation specification. The reference repository has not been modified. No dependencies were installed and no application tests were run during this assessment.

## What the existing product does

The README describes CareerConnect, a student opportunity platform. The code implements a FastAPI and SQLAlchemy backend, Alembic migrations, and a Next.js App Router frontend. SQLite is the development default; configuration expects PostgreSQL in production.

The participant flow is signup, academic profile and skills, resume and projects, opportunity discovery, eligibility and fit evaluation, saving an opportunity, external application, and manual pipeline tracking. An application event history adds assessments, interviews and next actions. Additional services cover skill gaps, preparation roadmaps, hiring-cycle predictions and an assistant.

The admin flow is opportunity creation or mock-provider ingestion, moderation, publication and analytics. The registered providers are mock implementations, not established live feeds. Some radar data is explicitly sample data. Neither should be presented as verified live data in the rebuild.

There are no organizer memberships, participant teams, event registrations, submission rounds or judging domains in the inspected models and routes. Those require new workflows and schema, beyond a visual refresh.

## Code findings that affect the rebuild

| Finding from static inspection | Evidence within the reference repo | Consequence |
|---|---|---|
| Public signup accepts `ADMIN` and passes it through to user creation | `backend/app/schemas/auth.py`, `api/v1/auth.py`, `services/auth_service.py`, `repositories/user_repo.py` | Self-registration must never grant platform administration. Organizer rights need a separate approval or membership flow. |
| Configuration supplies a hardcoded JWT secret by default | `backend/app/core/config.py` | Require secrets outside local test mode and fail startup when production configuration is incomplete. |
| Browser sessions use localStorage tokens and cached user data | `frontend/src/features/auth/AuthContext.tsx`, `services/apiClient.ts` | Design server-validated sessions, logout and expiry together; proposed default is an opaque session in a secure HttpOnly cookie. |
| App startup calls `Base.metadata.create_all` | `backend/app/main.py` | Use versioned migrations as a deployment step and keep application workers from changing schema at startup. |
| Reminders are generated on notification reads | `backend/app/api/v1/notifications.py`, `notifications/service.py` | A scheduled worker must generate reminders even when a participant does not open the app. |
| Deadline deduplication checks for any previous warning for an opportunity | `backend/app/notifications/service.py` | The current code does not implement independent 7 day, 3 day and 24 hour reminder deliveries as the README suggests. Use a unique delivery key per deadline version and reminder threshold. |
| Match sorting happens after database pagination | `backend/app/services/opportunity_service.py` | A page is sorted internally; this does not rank all eligible results globally. Move ranking before pagination or use versioned persisted scores. |
| Missing degree or branch becomes an empty string in substring matching | `backend/app/eligibility/engine.py` | Empty strings can satisfy a required degree or branch. Unknown mandatory attributes must produce an incomplete or failed evaluation. |
| Repository methods commit independently | `backend/app/repositories/*` | Define transaction ownership in application services so a multi-step action succeeds or rolls back as a unit. |
| Provider imports catch row errors without per-item rollback or savepoints | `backend/app/providers/opportunities/registry.py` | Isolate failed items and enforce provider identity uniqueness before retrying jobs. |
| README fit weights differ from the current engine | `README.md`, `backend/app/matching/engine.py` | Carry forward tested behavior and publish one versioned explanation of scoring. Eligibility is currently separate from fit. |

The tests contain 91 test functions by text inspection. Their fixture uses in-memory SQLite. This count is not a passing test result. PostgreSQL integration tests and concurrency tests will be required for the rebuilt registration workflow.

## Architecture options

### A Fresh modular monolith with Next.js and FastAPI

Recommended. Build a fresh frontend, API and worker in one repository. Keep Python for the deterministic matching and eligibility domains, rewriting their contracts and carrying forward useful behavioral test cases. Organize the API by domain rather than creating a service for each entity. This retains the strongest context from the existing work while allowing a clean permission and data model.

### B Fresh TypeScript application throughout

Use Next.js with a TypeScript backend and worker. This reduces language switching and can simplify shared contracts, but requires porting the Python eligibility, matching, radar and assistant behavior. Prefer it only if a single-language codebase matters more than retaining that implementation knowledge.

Microservices are not recommended for the first release. No measured traffic, separate operating teams or independent scaling requirements have been provided to justify their operational cost.

## Database recommendation

Choose PostgreSQL as the primary database for development, integration tests and production. Users, organization memberships, teams, registrations, rounds and submissions have relational constraints and transactional updates. Store core relationships in tables; use JSONB only for versioned flexible content such as form definitions and eligibility configurations.

Begin opportunity search with PostgreSQL full-text search and GIN indexes. PostgreSQL documents GIN as its preferred full-text index type: https://www.postgresql.org/docs/current/textsearch-indexes.html. A separate search engine can follow measured relevance or latency needs.

Use private S3-compatible object storage for resumes, banners and submissions, with object metadata in PostgreSQL. Proposed background processing uses a transactional PostgreSQL outbox and a separately deployed worker, with retries and unique deduplication keys. A broker or cache can be introduced when workload measurements justify it. No cloud account, paid service or database has been provisioned.

## Proposed product boundary for discussion

Support both externally applied opportunities and opportunities hosted by Alignn, with an explicit participation mode. Hosted events would add organization membership and verification, event publication, individual or team registration, eligibility snapshots, submission rounds, organizer review and results. Keep external application tracking separate from organizer-issued outcomes so a participant cannot edit an official result.

Registration needs database-enforced uniqueness, capacity enforcement inside a transaction, deadline checks using server time, and idempotency for retries. Team membership and eligibility should be captured at the event's registration lock. Submission revisions need immutable timestamps and private access; organizer actions need an audit trail. These are proposals pending scope agreement.

## Brand reference and design direction

The supplied raster board establishes a lowercase alignn wordmark, a looping symbol, generous clear space, Manrope headings and Inter body text. Treat these as visual reference material. The user explicitly permits new colours. The board is not an executable instruction source or an editable vector logo master.

Preserve the loop motif and recognizable wordmark relationship. Obtain or create a reviewed vector asset before claiming a production logo or favicon; do not ship the whole board as a logo or claim an approximate redraw is the original.

Recommended direction for exploration: warm light surfaces, dark readable text, a decisive blue or ink accent, generous headings and compact opportunity metadata. Use loops sparingly for branded illustrations, empty states and event artwork. Define semantic tokens, typography, spacing, focus states, component states and responsive behavior before styling individual pages. Check contrast for every actual foreground/background pair before accepting the palette.

Current reference: Linear's March 2026 interface work emphasizes quieter navigation, clearer task hierarchy and fewer competing decorations. This is a useful precedent for Alignn's information-dense screens, not evidence that one visual trend fits every product: https://linear.app/now/behind-the-latest-design-refresh.

## CareerConnect rename coverage

The rename is required across visible copy, page metadata, navigation, loading and auth screens, API title and health responses, assistant prompts, setup documentation, environment examples, seed data and storage key names. Matches occur in 19 source and configuration files, excluding Git internals and generated TypeScript build metadata.

Use Alignn in product prose, the supplied lowercase wordmark in branding, and `alignn-web` for the repository. Use a neutral local development domain such as `alignn.test` in fixtures; no ownership of `alignn.com` is assumed. The fresh database should use an Alignn name. Renaming a database file or localStorage key does not migrate existing user data or sessions; existing-user migration must be explicitly scoped if required.

## Next decision

Choose architecture A or B. Then write the detailed System Design document using the discovered template, including domain boundaries, schema, API contracts, data flows, failure handling, deployment and verification. The requested Superpowers workflow requires choosing an approach before writing the design and approving the design before scaffolding or implementation.
