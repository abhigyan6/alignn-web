# Preview, staging and production deployment design

12 November 2026. Proposed design for approval under Superpowers. No deployment workflow, host, DNS or provider setting has been changed by this design. Branch codex/deployment-pipeline is stacked on the separate CI and Git-hygiene tasks. Existing application changes are on codex/audit-vercel-recovery; do not push or merge main directly.

## Intent and current evidence

The user requested full-stack previews for each PR, automatic staging after main merges, manual approval for production, migration-before-release with failure stopping deployment, and a rollback runbook. They chose AWS app hosting, Heroku PostgreSQL and S3 files, formal planning, and accepted a separate manual production-promotion workflow if native GitHub reviewer gates are unavailable. For preview databases they asked for our recommendation: disposable per-preview PostgreSQL on a dedicated non-production AWS host is the engineering proposal for approval; staging/production retain distinct Heroku databases.

Current code has a manual main-only AWS ECR/SSM release workflow and one hard-coded host deployment script. That script already migrates before restarting services and attempts code rollback on failed health checks. It has no PR preview lifecycle, independent staging target or manual-promotion approval gate. Four deployment variable names exist in GitHub; their values and credentials were not read. The private repository has no configured environments; production environment lookup returns404. Account plan was not exposed, so reviewer support is not assumed. AWS host/resource health, credit balance and current provider configuration have not been inspected.

## Approaches

1. **Selected platform; proposed topology:** retain AWS containers and protected host deployment commands, with disposable PostgreSQL per PR and isolated production/non-production targets. Lowest migration impact; requires host capacity planning and sandboxing PR code. The user selected AWS/Heroku/S3; preview-container allocation remains our recommendation for approval.
2. One Heroku database add-on per PR would keep the same database provider but introduces per-open-PR provisioning, recurring cost and cleanup. Not recommended for the initial budget.
3. Frontend-only hosting previews or moving the whole product to another platform would not satisfy the selected full-stack target and are out of scope.

## Environments and isolation

- **Production:** production-only AWS target, Heroku database, S3 bucket/role and Clerk production instance. No PR workflow may read its credentials, assume its role or access its private network/files.
- **Staging:** a separately configured trusted non-production target, its own Heroku database, private S3 scope and Clerk development instance. Synthetic data only, no production database copy or production accounts. It receives successful main releases automatically.
- **PR preview:** unique immutable release per PR/head SHA, unique Compose project/network/volumes and disposable PostgreSQL database. Use synthetic seed data and isolated file storage. A dedicated preview host cannot also be the production or trusted staging host. No production secrets or data are inherited. Containers run without Docker socket, privileged mode, host networking or metadata/instance-role access. Apply non-root users, no-new-privileges, dropped capabilities, resource/log limits and per-preview network isolation. Host control-plane credentials stay outside PR containers.

Full-stack preview means web, API, worker, scanner and database are available and migrations run against the disposable database. Use a dedicated preview Clerk development instance with synthetic accounts and explicitly allowed preview callbacks; no production Clerk credentials. Any S3 testing uses only a PR-scoped temporary credential with a narrow disposable prefix, refreshed by a trusted host process outside PR containers; no host-wide credential is mounted. Mail goes to a preview-only sink with no real delivery. Disable public scraping schedules in previews; a fixture catalog is labelled as synthetic and never reaches staging/production ingestion.

Proposed hostnames are staging.alignn.onlyward.app and pr-<number>.preview.alignn.onlyward.app; these are proposals, not verified DNS. Require reviewed DNS/TLS configuration and private tester access before publishing preview URLs. A preview registry restricts proxy routes/certificate requests to real eligible PRs; arbitrary hostnames cannot create deployments. Confirm Clerk/OAuth callback support with a non-production sign-in smoke test before calling previews complete.

Actual host sizing, existing resource reuse and provider costs must be inventoried and approved before provisioning. Do not silently create paid add-ons or EC2 capacity. Every eligible PR queues for a preview; enforce configured resource limits and report capacity waits rather than deleting another open PR or claiming an undeployed URL is live. Scale capacity only after budget review.

## Trusted workflow boundary

Use separate CI/build, trusted publication, and trusted deployment jobs/workflows. Untrusted PR builds run on ephemeral GitHub-hosted runners without cloud/runtime secrets. Do not use pull_request_target to checkout or execute PR code, or put production credentials on a PR runner.

A trusted workflow from the protected default branch handles successful PR build artifacts. Bind repository ID, workflow/run ID, PR number and exact head SHA from GitHub's event/API, not PR-controlled shell text or artifact metadata alone. Validate artifact size, paths/symlinks and OCI metadata without executing it. Use fixed trusted scripts, parameter validation and immutable image digests. Re-check the PR head immediately before deployment; obsolete builds cannot replace newer previews. Fork/untrusted contributions receive no deployment credential automatically; require an explicit trusted authorization through the preview-only workflow before executing them on preview infrastructure.

OIDC publication/deploy roles are separate per environment, constrained to the trusted reusable workflow identity and environment/repository, narrow ECR repositories, fixed SSM documents and target hosts. Never grant an arbitrary SSM shell command or production access to preview roles. IAM updates require a reviewed change set before activation. The AWS toolkit MCP tools were unavailable during inspection; local AWS compute guidance and official provider documentation inform this proposal. No AWS API mutation has been made.

## Release flow

1. **PR:** CI passes for the exact PR head. The isolated unprivileged build produces API/web image artifacts. The trusted publisher transfers validated images into preview-only ECR repositories and emits an immutable manifest. The trusted preview deployer creates/updates that PR's environment, runs migrations, starts matching web/API/worker services and verifies readiness/web endpoints. Publish the URL only after success. New commits update only that PR. Closing a PR tears down its explicitly disposable resources through a trusted cleanup workflow. Expiry reconciliation handles missed events and does not target open/current previews or staging/production.
2. **Main:** a successful CI result for an exact main commit triggers staging. Build/publish the release, acquire deployment concurrency/host locks, migrate the staging Heroku database using the new API image, and only then activate the new code. Failed migration exits nonzero before service replacement. Preserve the prior serving image/config references. Health and non-production sign-in smoke checks determine staging success, which is recorded with the immutable manifest and commit.
3. **Production:** a human runs a dedicated promotion workflow from main and confirms the full release SHA. The workflow verifies caller authorization, main ancestry, a successful staging deployment for that exact release and manifest integrity. If native protected-environment approval is available, use it as an additional gate. workflow_dispatch is the agreed manual approval/promotion point; it is not described as independent two-person review. A push/merge alone never deploys production.

Current web images bake a public Clerk key at build time. Therefore build immutable staging and production web variants from the same source SHA/lockfile, with only the corresponding public configuration, before approval. The API image is shared by digest. The manifest binds both web variants, the API digest, source SHA and configuration identifiers. Staging does not prove byte-identical production frontend execution; production candidate build and environment-specific smoke tests remain required. No runtime secret is passed as a Docker build argument or included in artifacts. A separate runtime-config refactor is not silently added to this task.

Promotion runs production migrations using the approved new API image and production runtime configuration, then activates the matching production image pair and workers. Add per-environment GitHub concurrency and host/database migration locks. Do not cancel an in-flight migration. Artifact transport and deployment timeouts report unknown/in-progress status accurately and require checking the remote command before a retry.

## Migration failure and rollback

The release manifest records expected migration heads and backward-compatibility review. Production migrations must be expand/contract compatible with the previously serving version; destructive changes need a separately reviewed maintenance/backup plan. A completed migration is not automatically reversed if startup fails. Failure before migration success never activates new app containers. Run migrations exactly once under a lock; retries may safely re-run Alembic upgrade head but cannot bypass failure.

The current readiness implementation requires the image's exact migration head. This can make old images fail readiness after the database advances. Before claiming automated code rollback, implement and test an explicit schema-compatibility contract for releases participating in rollback, or restrict rollback to identical compatible heads. Unknown/incompatible versions fail closed. A bootstrap release of compatibility support must precede any release that relies on it; legacy images are not declared compatible by assumption.

Save current/previous immutable manifests and protected runtime config references only after a release passes health checks. On startup/health failure, restore the prior approved compatible images without running downgrade migrations. If compatibility or restored health fails, stop and escalate to a forward fix or explicitly approved backup restore. docs/runbooks/rollback.md documents the present manual procedure, safety checks and database limits; automation will follow the approved implementation plan.

## Files and acceptance

Expected changes: .github/workflows/deploy.yml; separate trusted preview/build/promotion/cleanup workflows; infra/release/deploy.sh generalized with validated environment configuration; dedicated preview/cleanup/rollback scripts and Compose/proxy templates; reviewed environment-scoped IAM templates; docs/runbooks/github-deploy.md and rollback.md; narrow schema-readiness compatibility changes/tests if required. No cloud manifest or workflow is considered active until its corresponding settings and roles are verified.

Acceptance requires actual isolated PR deployment/update/close cleanup; stale/fork artifact rejection; wrong-org/prefix/host-role denial; automatic staging after green main CI; no production deployment without the manual gate; failed migration proving old services remain; matching image digests and successful health/smoke tests; and a tested previous-version rollback with preserved data. Local mocked contract tests alone do not establish cloud deployment, isolation, approval enforcement or migration recovery.

## Inputs before activation

Verify account inventory and budget; approve host/resource changes; confirm staging/preview DNS, TLS and access; provision separate Heroku/S3/Clerk non-production configuration without revealing secret values; configure GitHub variables/roles and the manual promotion allowlist; verify backups/recovery capability. These can be prepared as reviewable IaC/configuration after design approval. Never ask for secrets in chat or silently consume production settings for previews.
