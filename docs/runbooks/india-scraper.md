# India-first scraper operations

Verified locally on 11 November 2026. Architecture stays Next.js/FastAPI/PostgreSQL with separate Python workers. This runbook does not establish production deployment, measured performance, remaining free credits or legal compliance.

## What updates the website

1. Open the private [scraper Actions page](https://github.com/abhigyan6/alignn-scraper/actions/workflows/scrape.yml), select **Run workflow**, `main`, and `all` or one enabled platform.
2. Matrix collectors validate public metadata, then upload the combined `alignn-opportunities-v1` artifact. Source counts distinguish success, partial, empty and failure. Repository identity is `1453961313`; workflow identity is `414656784`, path `.github/workflows/scrape.yml`.
3. The scheduler queues a GitHub poll every minute. The maintenance worker validates the private repository, workflow, branch, trigger, run/attempt, artifact identity/digest, archive bounds, schema and per-source data before updating PostgreSQL. Successful source receipts commit with their opportunity changes. Replayed imports do not duplicate records; older observations cannot undo a newer deadline/cancellation.
4. The next discovery request/refetch reads the database. An already open page needs a refetch/reload. No browser push update is promised.
5. A minute maintenance pass and read-time filters hide passed cutoffs/ends. Collection workers check up to twenty known records/source/cycle, including records missing from open indexes. An access error or absence from an index alone does not close a listing. Explicit cancellation/closure, elapsed actual dates, HTTP410 or two independent HTTP404 checks >=30 minutes apart can close it. Saves and application history remain.

The first verification [run](https://github.com/abhigyan6/alignn-scraper/actions/runs/43022085421) completed on 11 November. Backend receipts confirmed automatic import: HackIndia4 new active rows/11 past rows skipped, Luma13 new rows, Devfolio11 existing rows updated/2 skipped, Stripe1 existing row updated; the two other employer boards contributed no qualifying internships. These are a dated local observation, not a continuing count or complete coverage claim.

## Local services

Use the active `/Users/abhigyandwivedi/Developer/alignn-web` checkout, never the retained iCloud backup. Existing PostgreSQL/API/web services must run. In three terminals:

```sh
python3 scripts/local-scraper.py maintenance
python3 scripts/local-scraper.py collection
python3 scripts/local-scraper.py scheduler
```

The helper contains only repository/workflow identifiers and development flags. Existing `gh` login is consumed internally by the CLI; do not read/export its token. Never use CLI auth in production. These foreground services stop when their terminals/processes stop; keeping a Mac awake is not production supervision. Do not leave an older `--lane all` worker or scheduler running beside this setup. The scheduler performs startup catch-up on its first tick; no deployment hook is installed.

Check acknowledgement (not just GitHub green):

```sh
PYTHONPATH=apps/api/src apps/api/.venv/bin/python scripts/scraper-status.py
python3 scripts/local-status.py
```

Inspect receipt states, last import/verification, source errors and oldest due jobs. Logs/errors contain generic codes, never credentials, signed download URLs or raw source pages.

## Production activation still required

Set backend-only `SCRAPER_SYNC_ENABLED=true`, `SCRAPER_REPOSITORY=abhigyan6/alignn-scraper`, numeric repository/workflow IDs above, `SCRAPER_WORKFLOW_PATH=.github/workflows/scrape.yml`, `SCRAPER_BRANCH=main`, `SCRAPER_AUTH_MODE=token` and private `SCRAPER_GITHUB_TOKEN` with Actions-read access restricted to this one repository (or equivalent GitHub App access). A person enters/rotates the token privately in the server's secret configuration. Do not paste it into chat, GitHub collector code, frontend env or docs; agents must not inspect the value. The API's ordinary database configuration stays on the backend host.

Run the database migration, restart the API and supervise/restart both disjoint worker lanes plus scheduler. Confirm readiness and real receipts before enabling production import. Take/verify a database backup before migrations; deployment owner is the backend maintainer. A restore drill and representative production capacity/load tests are launch gates, not completed checks.

Cron jobs are gated by repository variable `SCRAPER_SCHEDULE_ENABLED=true`; leave unset until production readiness, source budgets and the account's actual Actions allowance are checked. Manual runs already work. GitHub scheduling can be delayed/dropped, and pending manual refreshes coalesce. No billing/pay-as-you-go settings are enabled here. No database credentials go to Actions. Single-host/worker/database downtime is accepted initially; this design is not highly available.

## Recovery and controls

- Stop import without deleting user data: set `SCRAPER_SYNC_ENABLED=false`, stop scheduler/new workers, drain/skip pending scraper jobs as appropriate. Do not restart old full-discovery jobs in production. Re-enable only after adapter/schema verification.
- Disable a faulty adapter by changing its static registry status, removing it from workflow choices/matrix, testing and exporting a new reviewed bot commit. Keep other sources working. Preserve last good rows with their true verification age. No automatic 72-hour suppression policy was approved.
- Schema1 imports only. Test a candidate collector against the installed importer before export. Preserve `EXPORT.json` origin SHA and `dirty:false`; do not hand-edit the export. A collector rollback must not restore an old user database or replay stale artifacts.
- Recovery import: download the final artifact, then `python -m alignn.domains.opportunities.import_scraped --file opportunities.zip --dry-run`, followed by the same command without `--dry-run`. This is fallback/recovery, not the normal update process.
- Older than24h artifacts are rejected; seven-day GitHub retention does not imply seven-day import freshness. If downtime exceeds24h, trigger a fresh workflow. Failed/rejected sources never erase an existing catalog. Unknown upstream failures remain visible in diagnostics, not labelled confirmed expiry.
- Jobs use existing five-attempt/24-hour lease/retry limits and terminal FAILED status. Artifact receipts expose RETRYABLE/FAILED outcomes; source receipts are retained30 days and terminal scraper jobs7 days, with bounded cleanup. Minute poll jobs share durable exponential backoff after GitHub failures, so new jobs cannot bypass a failed poll retry delay. Retry requires a reviewed fresh run or an explicit operator recovery, not deleting dedup receipts. Equal observed timestamps with conflicting contents reject the whole source partition.
- Review source terms/attribution before public launch. Robots/public access checks are not a legal or redistribution claim. Unstop, Hack2skill and KonfHub remain unavailable until verified permitted public contracts exist.

## Proposed monitoring and capacity gates

Proposed alert thresholds: no successful required-source import for12h; oldest import due >10min; >20% malformed/failing source observations for two runs; scheduler/worker heartbeat absent or repository access failure. These alerts are operator targets; no external alert delivery service was configured. GitHub collection green is not import acknowledgement.

Source allocation: Actions <=100 detail pages/source, one-second per-origin spacing, <=180s/source, max two source jobs; backend rechecks <=20 records/source/6h, persisted next-check ordering and source leases. Hosts do not share a global request semaphore. Honor robots/rate limits and reduce cadence when blocked. Minute poll metadata calls/runner minutes are a cost to check against real account limits; private Actions is not claimed unlimited/free.

Matching preserves global candidate ranking while fetching profile evidence once per rebuild and excluding/pruning inactive candidates. Before launch measure representative match-table size and rebuild latency:1000 users ×5000 matches can exceed1GB before indexes. Current small-catalog measurements cannot validate that scenario. No Redis, sharding, LocalStack or new paid infrastructure is introduced.

Dated local capacity sample (11 November):45 catalog rows and54 match snapshots; PostgreSQL total relation sizes including allocated indexes/TOAST were1,236,992 bytes for opportunities and114,688 bytes for match snapshots. This small existing dataset is not a load test or a per-row capacity guarantee.

Updated reviewed collector `add4020` also passed [run43056511188](https://github.com/abhigyan6/alignn-scraper/actions/runs/43056511188) and was acknowledged APPLIED by the restarted local worker. The workflow remains private and production cron remains gated off.
