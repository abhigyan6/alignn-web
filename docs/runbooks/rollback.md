# Roll back an Alignn release

This documents the existing Compose release layout and the proposed release controls. The new preview/staging/promotion pipeline is not installed yet. Verify the actual target, paths, deployed SHA and schema before executing commands; do not assume a stored template describes a running host.

## Choose the recovery path

1. Pause new releases for the affected environment. Record the failed workflow/SSM command ID and check its remote status before retrying anything. A workflow timeout does not prove the remote migration/deployment stopped.
2. Identify the last healthy release using its immutable API/web digests and Git SHA. Use the same environment's protected current/previous configuration; never use production files on staging/previews. Do not print env files or run docker compose config into logs.
3. Determine whether the migration failed before code activation, succeeded, or is still running. A failed migration should leave the previous services serving; check them before restarting anything. Do not run concurrent migrations or cancel one blindly.
4. Choose a code rollback only if the previous version is compatible with the current schema and runtime configuration. Keep a recoverable database backup before any data/schema recovery. Prefer a forward fix when rollback compatibility is unknown.

**Current limitation:** the API's readiness check requires its exact Alembic head. An old image can be alive but unready after a newer migration. Container startup is not proof of recovery. The future pipeline must test an explicit compatibility contract before advertising automatic rollback across different schema heads.

## Manual code rollback for the existing production layout

Run through the approved host-management path as an authorized operator. The paths below match the checked-in release script, not a verified live host. Adjust them only after inspecting the actual environment. This uses existing images and does not run Alembic downgrade.

```bash
set -euo pipefail
umask 077
runtime=/opt/alignn/runtime
manifest=/opt/alignn/releases/20261105/infra/staging/compose.aws.yaml
current="$runtime/deploy.env"
previous="$runtime/deploy.previous.env"
test -r "$current"
test -r "$previous"
test -r "$manifest"
exec 9>"$runtime/release.lock"
flock -n 9 || { echo "A release is still running; inspect it before proceeding."; exit 1; }

# Confirm schema compatibility before this step.
docker compose -p alignn --env-file "$previous" -f "$manifest" pull api web
docker compose -p alignn --env-file "$previous" -f "$manifest" \
  up -d --no-deps --pull never api web worker scheduler

# Both must succeed, plus the signed-in smoke test below.
curl --fail --silent --show-error --max-time 15 \
  --resolve alignn.onlyward.app:443:127.0.0.1 https://alignn.onlyward.app/api/ready
curl --fail --silent --show-error --max-time 15 \
  --resolve alignn.onlyward.app:443:127.0.0.1 https://alignn.onlyward.app/explore >/dev/null
```

If the old images fail readiness, do not label the rollback successful or loop through restarts. Preserve logs with credentials redacted and use the forward-fix/database-recovery decision below. Avoid deleting volumes, changing DNS or recreating the database as a troubleshooting shortcut.

After successful health and authorized non-sensitive smoke checks (sign-in, profile, listing read, saved/application read), record the rollback SHA/digests and update the protected deployment pointer atomically while still holding the deployment lock. Preserve the failed release references for diagnosis. Keep both image pairs in ECR until recovery is verified. With the existing layout an operator can exchange the current/previous env files using protected temporary copies; never print their contents. The proposed automation will manage these pointers through validated release manifests.

## Database recovery

Do not automatically run alembic downgrade: that can destroy data and is not implied by an application rollback. If a forward fix is impossible, obtain explicit approval for the backup/restore point and potential lost writes. Verify the backup timestamp and provider restore procedure/capability for this database plan. Restore into a separate recovery database first, migrate/test the chosen application version there, validate integrity and access controls, then perform a reviewed connection switch. Do not overwrite the only database copy.

This runbook does not claim measured RPO/RTO or that backups were tested. If current provider restore capabilities or credentials are unavailable, state that blocker rather than invent a restore command.

## Preview and staging recovery

Use only that environment's manifest, database and files. A broken PR preview can be recreated from its head SHA and synthetic data after confirming the resources are explicitly disposable. Cleanup must validate PR ownership and cannot match production/staging paths or volumes. Staging rollback follows the same compatibility and health checks as production, with its own Heroku database and private storage scope.

## Before re-enabling releases

Confirm the remote deployment command finished; record actual serving SHA/digests, database schema and health; complete an appropriate smoke check; preserve sanitized incident evidence; and fix or revert the failing change through a new branch and PR. Never push a hotfix directly to main.
