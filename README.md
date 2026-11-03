# Alignn

An opportunity and participation platform for students, teams and organizers.

Alignn brings together opportunity discovery, explainable eligibility, application tracking, team registration, submission rounds and organizer-reviewed results.

## Project status

The architecture and marketplace design direction were approved on 3 November 2026. This repository currently contains the approved specification, implementation plan and visual reference. The application has not been implemented yet.

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

Local setup commands will be added with the first working milestone. Production deployment, paid services and migration of existing users are outside the current repository setup.
