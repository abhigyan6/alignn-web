# AWS application host with Heroku PostgreSQL

This is the latest hosting direction approved in chat on 5 November 2026. It supersedes the Heroku API placement in `heroku-staging.md` and the all-AWS/RDS proposal. Run Next.js, FastAPI, worker and scheduler as separate processes on one AWS host initially; keep the existing Heroku Essential-0 database. No Heroku Basic API dyno is needed. Do not upgrade the database without measured need and a budget decision.

## Prepared files

- `apps/web/Dockerfile`: Node 24 production Next.js server built from the root npm workspace. The public Clerk key is build-time; secret values are runtime-only. Root `.dockerignore` excludes environment files, Git history and local credentials.
- `infra/staging/compose.aws.yaml`: prebuilt API/web images, HTTPS Caddy proxy, private API/worker/scheduler/scanner services and a release-only migration command. Only proxy ports 80/443 are published. Pin reviewed image digests before release.
- `infra/staging/Caddyfile.aws`: same-origin `/api/*` forwarding directly to FastAPI. Scanning and application ports have no host bindings. Configure the actual domain in Clerk and PUBLIC_ORIGIN.

The pool settings permit at most five connections per API/worker/scheduler process, with room for one release process under Heroku's 20-connection limit. Run one of each; avoid overlapping migrations and extra processes. A pool ceiling alone does not establish performance.

## Infrastructure and runtime gates

1. Refresh the dedicated IAM login, verify the assumed role, inventory current resources and remaining credits. The historical inspection role is not assumed to have deployment permissions. Do not replace it with root or attach AdministratorAccess.
2. Select a region after checking available scoped access, latency to Heroku Europe and pricing. A Mumbai deployment is not assumed optimal. Confirm the owned HTTPS hostname and DNS access.
3. Prepare a reviewed CloudFormation change set for a single encrypted host, private S3 storage, restricted instance role, IMDSv2, Session Manager and bounded logs. No new RDS, public SSH, NAT gateway or load balancer is required for this initial topology. Review any public web ingress explicitly; restrict staging to testers where feasible.
4. Build and verify architecture-compatible images away from the serving host. Docker is not currently installed on the development Mac, so the new container build is unverified. Do not treat this manifest as an already running deployment.
5. Complete instance-role S3 support: current application production guards and object adapter still require explicit storage keys. Do not embed keys in images/user data or put placeholder values into production settings. Runtime secret delivery and role permissions must be implemented/reviewed before launch.
6. Supply private runtime configuration on the host with restricted file ownership/permissions. The example manifest expects externally provisioned runtime files; it does not implement secret retrieval. Never commit these files or print resolved `docker compose config` to chat/logs. Container environment is readable by host/Docker administrators; scope access accordingly.
7. Configure the authentic provider CA chain and verify `verify-full` from the application container. Do not override SSL mode with a weaker database-URL query parameter. Current TLS 1.3 psql evidence establishes encryption, not full application certificate verification.
8. Configure authenticated application mail, private upload CORS, scanner readiness/signature updates, process health checks/alarms and production Clerk credentials. A running scanner container is not proof it is ready.
9. Migrate once with the release profile after all settings are valid; start services from matching revisions; verify readiness and the complete browser/upload/worker flow. Keep development fixtures out of production. Test restore and rollback before removing maintenance/access restrictions.

Example release sequence after all gates pass (not executed by this preparation):

```sh
docker compose --env-file /etc/alignn/deploy.env -f infra/staging/compose.aws.yaml pull
docker compose --env-file /etc/alignn/deploy.env -f infra/staging/compose.aws.yaml --profile release run --rm migrate
docker compose --env-file /etc/alignn/deploy.env -f infra/staging/compose.aws.yaml up -d
```

`deploy.env` contains the image references, actual domain and host paths required by the manifest. Application runtime files hold the separate service configuration. They are provisioned securely, not copied from the development checkout. A successful pull/start is not product acceptance.

Sources: https://nextjs.org/docs/app/guides/self-hosting ; https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/ . New infrastructure, container builds, ARM execution, email, S3 instance-role access and public launch remain unverified.
