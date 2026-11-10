# Alignn releases from GitHub Actions

The first release is manual. After the first run and signed-in smoke tests pass, add a `push` trigger for `main` to [the release workflow](../../.github/workflows/deploy.yml). Both triggers use the same checks and release job. Treat every change to workflow or Docker build files on `main` as production code.

## One-time administrator setup

1. In IAM, reuse the GitHub OIDC provider for `token.actions.githubusercontent.com` with audience `sts.amazonaws.com`, or create it if it is missing. Review [GitHub's AWS OIDC setup](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws). The checked-in trust condition uses this repository's immutable owner/repository IDs and the `main` branch. Verify the subject configuration before creating the role.
2. In Mumbai, review a CloudFormation change set for a new `alignn-github-release` stack from `infra/release/github-deploy.cfn.yaml`. Set `InstanceId` to the verified Alignn host, `GitHubProviderArn` to the IAM provider ARN, and `GitHubSubject` to the exact allowed value in the template. Acknowledge IAM creation. The change set should create two private ECR repositories, one scoped IAM role, and one SSM command document. Review [ECR storage pricing](https://aws.amazon.com/ecr/pricing/) before execution.
3. Update the existing `alignn-host-access` stack. Download its current **original** template through CloudFormation, then run `python3 infra/release/allow-runtime-ecr.py current-template.json updated-template.json`. Use the generated template to create an update change set, reusing the stack's parameters. The only expected changes are to `RuntimeRole` and `RuntimeBoundary`. Execute after reviewing the change set. The host will be able to pull images from the two Alignn repositories.
4. Through the existing administrator-controlled SSM access, install `infra/release/deploy.sh` as root at `/opt/alignn/release-tools/deploy.sh` with mode `0755`. Confirm the SSM Agent supports environment variable interpolation for command parameters, Docker Compose is installed system-wide, and the host has AWS CLI v2, `flock`, and `curl`.
5. Create the root-owned `/opt/alignn/runtime/deploy.env` with mode `0600`, using the currently running image references and host paths. Use the host's existing API/web runtime env files and PostgreSQL CA. The file should have the following keys. Verify the active Compose project is `alignn`, the manifest is at `/opt/alignn/releases/20261105/infra/staging/compose.aws.yaml`, and Caddy is serving the expected hostname. Adjust the fixed host paths in the reviewed script first if the live host differs.

   ```dotenv
   ALIGNN_API_IMAGE=<currently-running-api-image>
   ALIGNN_WEB_IMAGE=<currently-running-web-image>
   ALIGNN_SCANNER_IMAGE=<currently-running-scanner-image>
   ALIGNN_PROXY_IMAGE=<currently-running-caddy-image>
   ALIGNN_API_ENV_FILE=/opt/alignn/runtime/api.env
   ALIGNN_WEB_ENV_FILE=/opt/alignn/runtime/web.env
   ALIGNN_POSTGRES_CA_FILE=/opt/alignn/runtime/postgres-ca.pem
   ALIGNN_HOSTNAME=alignn.onlyward.app
   ```

6. Under GitHub repository **Settings → Secrets and variables → Actions → Variables**, add these four variables.

   | Variable | Value |
   | --- | --- |
   | `ALIGNN_DEPLOY_ROLE_ARN` | CloudFormation output `DeployRoleArn` |
   | `ALIGNN_DEPLOY_DOCUMENT` | CloudFormation output `DeployDocumentName` |
   | `ALIGNN_DEPLOY_INSTANCE_ID` | The verified instance ID used in the stack |
   | `ALIGNN_CLERK_PUBLISHABLE_KEY` | The production Clerk **publishable** key for the build |

The GitHub role uses short-lived AWS credentials. Runtime credentials stay in the existing protected files on EC2. The SSM command accepts two image digests and a Git SHA, and executes the fixed host script.

## First release and verification

1. Merge the reviewed app and workflow PR into `main`. Confirm that the migration is compatible with the previous release, and that a recent PostgreSQL backup can be restored.
2. From **Actions → Deploy Alignn → Run workflow**, select `main`. The workflow reruns CI, builds the images for ARM64, and publishes them by digest. It then runs migrations and starts the matching web/API/worker/scheduler images. The host and the GitHub runner check `/api/ready` and `/explore`.
3. Check a returning account goes to the workspace and a new account can finish onboarding, optionally upload a private resume, and track an external application. Verify scanner and worker processing with non-sensitive fixtures before enabling automatic releases.

## Failure and rollback

A failed build or pull leaves serving containers in place. A failed migration stops the release before the restart. A failed restart or host-local health check attempts to restore the previous images. Inspect the SSM command ID from GitHub before retrying if status polling times out. The workflow does not automatically downgrade the database. If the previous API requires an exact older schema revision, restoring the previous images may still leave readiness failing. Review the migration and recovery options before choosing a database rollback.

The host records the last successful Git revision in `/opt/alignn/runtime/deployed-revision` and keeps the previous Compose image references in `deploy.previous.env`. Keep the previous images in ECR until a newer release is verified.
