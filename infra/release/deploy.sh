#!/usr/bin/env bash
set -euo pipefail
umask 077

readonly api_digest="${1:?API digest required}"
readonly web_digest="${2:?Web digest required}"
readonly revision="${3:?Git revision required}"
[[ "$api_digest" =~ ^sha256:[0-9a-f]{64}$ ]]
[[ "$web_digest" =~ ^sha256:[0-9a-f]{64}$ ]]
[[ "$revision" =~ ^[0-9a-f]{40}$ ]]

readonly runtime=/opt/alignn/runtime
readonly current_env="$runtime/deploy.env"
readonly compose_file=/opt/alignn/releases/20261105/infra/staging/compose.aws.yaml
readonly domain=alignn.onlyward.app
export AWS_REGION=ap-south-1 AWS_DEFAULT_REGION=ap-south-1 AWS_PAGER=""
[[ -r "$current_env" && -r "$compose_file" ]]
exec 9>"$runtime/release.lock"
flock -n 9 || { echo "Another Alignn release is running."; exit 1; }

account="$(aws sts get-caller-identity --query Account --output text)"
[[ "$account" =~ ^[0-9]{12}$ ]]
readonly registry="$account.dkr.ecr.$AWS_REGION.amazonaws.com"

next_env="$(mktemp "$runtime/deploy.env.XXXXXX")"
docker_config="$(mktemp -d)"
trap 'rm -f -- "$next_env" "$docker_config/config.json"; rmdir -- "$docker_config" 2>/dev/null || true' EXIT
export DOCKER_CONFIG="$docker_config"
aws ecr get-login-password | docker login --username AWS --password-stdin "$registry" >/dev/null

# Copy the approved Compose settings and replace only the API and web digests.
awk '!/^[[:space:]]*(ALIGNN_API_IMAGE|ALIGNN_WEB_IMAGE)=/' "$current_env" > "$next_env"
printf 'ALIGNN_API_IMAGE=%s/alignn-api@%s\nALIGNN_WEB_IMAGE=%s/alignn-web@%s\n' \
  "$registry" "$api_digest" "$registry" "$web_digest" >> "$next_env"

compose() {
  local release_env="$1"
  shift
  docker compose -p alignn --env-file "$release_env" -f "$compose_file" "$@"
}

healthy() {
  local attempt
  for attempt in {1..24}; do
    if curl -fsS --max-time 4 --resolve "$domain:443:127.0.0.1" \
        "https://$domain/api/ready" >/dev/null 2>&1 &&
      curl -fsS --max-time 4 --resolve "$domain:443:127.0.0.1" \
        "https://$domain/explore" >/dev/null 2>&1; then
      return 0
    fi
    sleep 5
  done
  return 1
}

echo "Preparing Alignn release $revision"
compose "$next_env" pull api web
# Release migrations must remain compatible with the previous app during rollback.
compose "$next_env" --profile release run --rm --no-deps migrate
if compose "$next_env" up -d --no-deps --pull never api web worker scheduler && healthy; then
  cp -- "$current_env" "$runtime/deploy.previous.env"
  mv -- "$next_env" "$current_env"
  printf '%s\n' "$revision" > "$runtime/deployed-revision"
  echo "Alignn release $revision is ready."
else
  echo "Release failed its startup or health check. Restoring previous images."
  if compose "$current_env" up -d --no-deps --pull never api web worker scheduler && healthy; then
    echo "Previous images are serving again."
  else
    echo "Previous images did not pass health checks. Operator intervention is required."
  fi
  exit 1
fi
