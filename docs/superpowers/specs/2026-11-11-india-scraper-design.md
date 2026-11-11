# India-first opportunity bot and private manual Actions

Status: draft for user approval. Date: 11 November 2026.

## Intent and agreed decisions

Alignn is an India-first career opportunity discovery product. The user explicitly requested removing Remotive, adding more India-focused event platforms, publishing the scraping bot privately on their GitHub account and providing a manual GitHub Actions trigger. They selected the Superpowers workflow and initially selected **private JSON artifact plus local backend import**. Their latest request extends this to **automatic production import and source-expiry checks**; manual import remains a local/recovery path. Hosting, authentication and the existing Next.js/FastAPI/PostgreSQL modular monolith remain unchanged. No LocalStack or Docker setup is needed for this work.

GitHub CLI's account lookup returned `abhigyan6`. Proposed repository name (builder choice): `abhigyan6/alignn-scraper`, private. This document is not evidence that it has been created. No credentials or private account files may be read, printed, copied into the repository or requested in chat.

## Current implementation and change boundary

`apps/api/src/alignn/domains/opportunities/ingestion.py` currently schedules Remotive, Devfolio and three Greenhouse boards. The separate worker dispatches these jobs using the PostgreSQL queue. Devfolio crawls public catalog/detail pages with Scrapy and requires explicit India country data; Greenhouse filters internships to a curated set of Indian locations. Both upsert by source identity. The running website reads public opportunities from PostgreSQL; publishing a scraper artifact alone will not update it.

Current source collectors import application database/model modules, so they cannot simply be copied to GitHub Actions without also bringing database configuration. Extract a standalone `alignn_scraper` Python namespace alongside `alignn` under `apps/api/src`; it must never import `alignn`, SQLAlchemy, Clerk, application settings or any database adapter. Include that namespace in the API wheel. This preserves existing Docker/API build structure without a new local-path package dependency. Existing application source wrappers call the standalone collector, then perform application-owned persistence.

Source code in the app checkout is the maintained source; the private bot repository is a reproducible export of the standalone namespace, its focused tests, package metadata and workflows. Provide an explicit export/update procedure. Never create divergent hand-edited copies without recording which app commit they came from. The bot repository must not include `.env`, `.superpowers`, uploads, raw fetched pages, user fixtures, app Git history or cloud configuration.

## Approaches considered

1. **Private artifacts with production worker pull — recommended revision.** GitHub collects data without database access. The deployed Python worker polls the private repository, validates a completed approved run, downloads its artifact and invokes the same backend importer automatically. The API host needs narrowly scoped repository Actions-read access. The existing local/manual import remains available for testing and recovery.
2. **GitHub pushes to a deployed ingestion endpoint — not recommended initially.** Requires another externally reachable machine-authenticated write endpoint, delivery retries and replay controls. Worker pull reuses the existing background processing and can recover after downtime without adding that endpoint.

The latest user request authorizes designing automation, not a claim that production hosting or repository credentials are already configured. Production worker-pull is the proposed implementation choice to approve in this revised design.

Within the selected approach, reuse Scrapy and the existing Python interpreter rather than add an LLM browsing agent, browser automation package, database on the Actions runner, Redis or another queue. No dependency additions are assumed until the package manifest and lock are reviewed.

## Sources and verification gates

Retain Devfolio and India-targeted Greenhouse internships. The user expanded the required event-platform targets to **Unstop, HackIndia, Luma and Hack2skill**. KonfHub is another priority. Investigate HackerEarth, Devpost, MLH, Townscript, Eventbrite and public developer-community calendars as subsequent sources for Indian career/technical events. This is an extensible source registry, not a claim that every popular platform has a working adapter.

Each registry entry must state its verified access method, supported categories, India evidence, last successful check and one of `enabled`, `needs_verification`, `blocked` or `unsupported`. Only verified enabled adapters appear as runnable source choices. Named targets must remain visible in documentation if blocked; do not silently substitute an unrelated source or claim complete coverage. Broad event platforms must be filtered to career, student, technical and builder events in India; entertainment listings are out of scope. Failed/unsupported sources are explicitly reported in an all-source run, not silently treated as successful empty catalogs. Do not ship a configured placeholder as a working source.

Evidence collected:

- Devfolio's public catalog/detail extraction already ran successfully locally. Country `India` is explicitly required. Event dates must remain distinct from registration cutoffs.
- `https://hackindia.org/hackathons` returned public server-rendered open listings. An inspected detail page includes Event JSON-LD with `addressCountry: IN`, actual start/end datetimes and published registration-date fields in its page state. Its robots file allows public pages and disallows `/api/` and private areas. Do not fetch those API/profile/team routes.
- `https://konfhub.com/events` is public, but its initial HTML does not include the catalog data. Verify a permitted public discovery path and event metadata before enabling its adapter. Public sitemap/detail extraction is an option; do not touch attendee/registration APIs. A KonfHub adapter is accepted only after an actual future Indian event parses successfully with provenance.
- Unstop is a required target. A direct public catalog fetch returned a JavaScript/cookie shell. This establishes neither a working parser nor permission to use undocumented authenticated endpoints. Verify an allowed public extraction method; report a blocked adapter if unavailable.
- Luma is a required target. Official public event pages were found for India-specific hackathons, including `https://luma.com/wrnbcpzs` with an explicit Indian audience and a published registration cutoff. This is evidence for a detail parser, not proof of complete platform discovery or public API access. Verify robots, source terms, bounded discovery and date/metadata extraction before enabling. Do not follow attendee, registration or private-location routes.
- Hack2skill's homepage is public, but its listing/detail URLs returned only a JavaScript application shell in this probe. Earlier search snippets are not proof of an ingestion contract. Keep it disabled unless a permitted public structured source is established.

Implement verified adapters for the required named platforms wherever permitted public access can be established. At least two additional verified event-platform adapters beyond Devfolio are required for the first expansion checkpoint; a dead or mock adapter does not satisfy it. Continue recording unresolved named platforms as incomplete work rather than calling the whole requested platform set complete. Document any additional sources before enabling them. Source terms/attribution must be reviewed and recorded before publication; robots allowance and HTTP 200 are not legal assurances or redistribution licences. Do not claim compliance.

Every imported event requires explicit Indian country metadata, or an auditable official location/audience statement supported by its adapter. Platform branding, APAC, timezone, language, currency or online format alone are insufficient. For employer listings, retain the explicit curated Indian city/country test and its limits; this is location relevance, not a guarantee of nationality/student eligibility. Unknown or conflicting geography is skipped and counted. Only technical, career, education or builder events belong in scope; no sports/entertainment bulk feed.

## Standalone collector contract

The bot supports `python -m alignn_scraper --source all --output output/opportunities.json`; `--source` accepts only the configured source names. Each source has a fixed allowlist of HTTPS hosts and permitted path forms. No arbitrary URL input, credentials, login, browser cookies, proxy rotation or CAPTCHA bypass.

Reuse an identified user agent and robots handling. Proposed upper bounds: one active request per domain; at least one second between requests; 15-second request timeout; two MiB decompressed HTML per page; one retry; at most 100 detail pages per event platform; 180 seconds per source, with sources isolated into a bounded Actions matrix (maximum two source jobs concurrently, ten minutes per source job). The default all-source run explicitly reports the enabled/blocked source set. A report/merge job combines only validated source outputs. This avoids serial starvation as the source registry expands. Scheduled collection is a proposed production-only six-hour cadence; no free-runner quota is assumed and scheduling stays disabled until runner allowance and production readiness are checked. Restrict redirects and prevent metadata/private-address fetches. Public outbound application URLs are validated and retained but never followed to submit applications.

Output is UTF-8 JSON with `schema_version: 1`, timezone-aware UTC `generated_at`, source reports and a normalized opportunity list. Each source report includes a fixed source key, status (`ok`, `partial`, `failed`, `empty`), successful check time, accepted/skipped/failed counts and generic error codes. Rows retain source name, stable source ID, canonical source/application URL, title, plain-text description, organizer/employer name when published, category, location, explicit country evidence, known work mode and actual registration/start/end timestamps. Use `null` for unknown timestamps; never convert event end dates to application deadlines. Inferred skills remain preferences; do not invent eligibility, stipends, verification or organizer endorsement.

Use the same normalization in Actions and local scheduled jobs. Deduplicate within each source using its stable ID/canonical URL. Do not merge similarly titled events across platforms without reliable shared identity. Do not emit participant objects, personal contact fields, profiles, images, full page state or raw HTML. Application/user data never enters the collector.

A partial source may contribute its individually validated rows, marked partial. Failed/empty source results must be visible in the report rather than silently appearing successful. Preserve diagnostics as error codes/counts, not raw responses. Nonzero exit when every requested source fails; a run with some failed sources is labeled degraded, with a valid artifact and explicit summary.

## Backend import and Remotive retirement

Add a backend-owned CLI, proposed `python -m alignn.domains.opportunities.import_scraped --file /path/to/opportunities.json`, with `--dry-run` support. Reads a local file only; never evaluates code or fetches supplied URLs. Use an explicit import allowlist and strict schema. Maximum artifact size ten MiB, maximum 1,000 records; reject unsupported versions, stale artifacts older than 24 hours, generation times over five minutes in the future, duplicate IDs, mismatched source reports, invalid country evidence, unsafe URLs and malformed dates before any writes. Invalid input must leave existing data unchanged.

Dry-run validates and reports counts without writes. Actual import occurs through the API's Python domain modules using a transaction, source lock, idempotent source identity and source-check ordering. Older per-source snapshots cannot overwrite newer data. Assign fresh ingestion time separately from original source check time where appropriate; never make old data appear freshly fetched. Re-importing identical data must not create duplicates or increment opportunity versions unnecessarily. Recompute inferred preferred skills from the existing local catalog before version comparison; changing deadlines increments deadline version. Leave organization verification false for feed-created organizations.

Public catalogs are often curated/partial: missing records do not establish closure. Close an imported record when its sourced deadline/end has passed or the source explicitly says it is closed/cancelled. Skip ended/closed events on new import. Imported source success must not reopen retired Remotive data.

Remove Remotive listings from discovery and search, including existing imported listings, not just future ingestion. Remove Remotive scheduling and network-fetch behavior. Drain queued historical `ingest_remotive` jobs as no-ops so old jobs cannot republish data. Retire existing Remotive rows by changing status to CLOSED and bumping version only when necessary; preserve opportunity IDs, saves and application history. Add a query exclusion as protection until all old workers are restarted. Do not delete those records or their linked user data. Update source/runbook documentation so Remotive is clearly retired rather than offered as an active command.

Local development can retain direct source jobs. In production GitHub Actions owns new-listing discovery; the existing Python worker owns artifact import, expired-date maintenance and bounded rechecks of known source listings. Avoid running duplicate full discovery crawls in production. All paths share normalization/import rules.

## Private repository and manual Actions

Create the reviewed export as a private repository under `abhigyan6`. Verify repository privacy and the remote before pushing. No public publication, deployment or DNS changes. Record export origin/commit in the bot README.

Workflow `Scrape Indian opportunities` has `workflow_dispatch`, a choice input for `all` or an enabled source, a single workflow concurrency group and bounded per-source matrix jobs with ten-minute timeouts (maximum two concurrent source jobs). Keep manual `workflow_dispatch` and add a production-gated six-hour cron trigger after allowance/readiness verification. GitHub scheduling can be delayed; this is not an exact-time freshness guarantee. A source-specific manual choice runs only that enabled adapter; `all` runs the enabled registry and reports blocked/unverified targets separately. Runner: GitHub-hosted Ubuntu with Python 3.12. Pin reviewed action revisions, use `contents: read`, disable persisted checkout credentials, and install only the standalone bot's locked dependencies. Do not expose database ports or give database, AWS, Clerk or Heroku credentials to Actions.

Run fixture tests before scraping. Upload only `output/opportunities.json` plus a sanitized source report as a private Actions artifact, retained seven days; write source counts/status to the job summary. Never put untrusted source text in shell commands or interpret it as GitHub workflow output. A verification manual run is authorized by the requested functional workflow; check the account's Actions restrictions/availability, do not claim remaining free minutes or enable paid runners/billing.

## Automatic production handoff

Recommended sequence: manual **Run workflow** or production-enabled cron -> per-source fetch/validation -> private artifact -> production worker poll -> backend import -> PostgreSQL -> next discovery read.

The production worker checks every 60 seconds (proposed cadence) using a fine-grained token restricted to **Actions: read on the scraper repository**, or an equivalent GitHub App installation token. A human configures this privately on the backend host; never put it in frontend variables, scraper code or chat, and never inspect it through agent tools. No Heroku/PostgreSQL connection string is supplied to GitHub Actions. The worker uses its existing server-side database configuration, whichever environment is actually deployed.

Pin the expected repository numeric identity, workflow identity/path, default branch and allowed trigger types. Only import completed, trusted default-branch runs; ignore pull-request/unapproved-branch artifacts. Do not rely on artifact filename alone. Use a fixed artifact name, artifact ID and available digest, safe bounded ZIP handling (ten MiB uncompressed JSON cap, no path traversal/symlink extraction) and the strict schema/freshness checks above. Paginate run/artifact enumeration with a persisted cursor so busy periods and downtime cannot cause silent skipped imports.

Persist run/source outcomes and import deduplication in PostgreSQL. Source check times determine update order, so an older all-source run cannot overwrite a newer source-specific result. Failed downloads/imports retry under existing worker retry limits, with visible terminal failure. A failed source does not erase existing rows. In a degraded run, import only separately validated successful/partial source data and record failures; a green GitHub collection run is not proof of successful backend import.

On deployment/startup, enqueue a catch-up poll and expire known passed deadlines. Import only eligible unprocessed artifacts within the 24-hour freshness window; do not present an older artifact as newly fetched. If no fresh artifact exists, retain existing data with its real age and report that collection/import is pending. Artifact retention is seven days, not a seven-day import freshness promise. Production credentials and the always-running worker must be present before automatic delivery can be called working.

After import, normal discovery reads use updated PostgreSQL rows and invalidated profile matches are recomputed by the existing queue. Current client views update on reload/refetch; live browser push updates are not part of this change. Any future public catalog cache must be invalidated when the import commits.

Manual local/recovery flow remains: Actions -> completed run -> download artifact -> backend `--dry-run` -> backend import -> reload discovery. A GitHub runner cannot reach the Mac's `localhost`; automatic local import is possible only when a configured local worker is awake/running and has the scoped repository-read access.

## Expired and closed opportunity handling

Every collection/import cycle checks dates and explicit statuses, and also enqueues bounded source rechecks for previously active listings from the selected sources. This inventory comes from the application's database; the crawler repository receives no user records. The database worker resolves each stored source ID to its already validated canonical URL and applies the same source allowlist/robots/rate/time controls. Pages absent from an open-events index are individually checked rather than presumed expired. Large inventories are paginated/queued across runs, with counters for due, checked, remaining and failed; do not claim complete expiry checks if the budget was exhausted.

A separate minute-cadence backend job closes known elapsed registration deadlines or ended events without waiting for GitHub. Public discovery filters must enforce those date rules at read time as well, including events with unknown registration cutoff but a known elapsed end time. Passing a start date alone is not evidence that applications closed.

Decision rules:

- Published registration cutoff passed, or event end passed: close/hide from active discovery; preserve the source timestamps and reason.
- Explicit, successfully parsed registration-closed/cancelled status: close/hide with the source-check time and reason.
- HTTP 410 for the known canonical page: close as removed. For HTTP 404, require two independent checks at least 30 minutes apart before closing as removed; reset the observation when a valid page returns.
- Missing from catalog, unknown deadline, redirect, 403, 429, timeout, parser failure or upstream 5xx: do not infer closure; preserve the row, mark its verification stale/failed and retry within the source budget. An inaccessible page is not proof of expiry.
- A verified deadline extension or reopening can update/reopen an ordinary source record only with newer source evidence and dates that are still valid. Retired Remotive rows can never reopen through import.

Expired/removed records remain available to the user's saved/application history with closed status; do not delete those relationships. Store generic closure/recheck metadata, not raw pages, participant details or user data in artifact logs. Report newly added, updated, expired, removed, unchanged, skipped and failed checks separately.

References: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule and https://docs.github.com/en/rest/actions/artifacts.

## Acceptance and verification

- Tests first for Remotive job retirement, exclusion, status update and preservation of saves/application history.
- Fixture tests for each platform's true geography, unknown/misordered/expired dates, source changes, malformed/duplicate IDs, partial responses and personal-field exclusion. Include at least one live successful future India event per new adapter; fixture success alone is insufficient.
- Standalone tests run without application modules, app configuration, database services or credentials.
- Real PostgreSQL import tests use only the dedicated test database and exercise dry-run, idempotency, freshness ordering, all-or-nothing validation, partial manifests, deadline versioning and expired/cancelled listing handling.
- Workflow syntax/config checks; verify private repository setting, default-branch workflow visibility, successful manual dispatch and a downloadable valid artifact. Treat blocked/failed upstream sources as failures rather than fabricated coverage.
- PostgreSQL tests for automatic import idempotency, concurrent pollers, trusted workflow/branch validation, bounded ZIP handling, retry recovery, cursor pagination, stale artifacts and out-of-order source-specific/all-source runs.
- Expiry tests for elapsed deadlines, ended events with unknown cutoff, explicit closure/cancellation, newer reopening, two spaced 404 checks, 410 removal, blocked/rate-limited pages, partial inventory coverage and preservation of saves/application history.
- Import the verified artifact into the confirmed local app database, restart relevant background services, and check Indian discovery through the running API. Test production handoff using a controlled environment only after the required scoped access is privately configured. No production import/deployment is implied by local tests.

## Scope exclusions and open items

No event hosting, registrations, teams, judging, auto-applications, resume transmission, new auth flows, AI eligibility decisions or scraper dashboard. No new cloud infrastructure, LocalStack, database move or claim of complete India coverage.

Builder choices: source-specific parsing selectors, internal module names, fixture sanitization and export mechanics may be decided during the implementation plan, preserving these contracts. Unverified platform access is a source gate, not permission to bypass restrictions. Exact source substitution must be recorded if KonfHub fails its gate. Repository creation or an external Actions run blocked by account permissions must be reported accurately; source validation work can continue independently.
