# India-first opportunity bot and private manual Actions

Status: draft for user approval. Date: 11 November 2026.

## Intent and agreed decisions

Alignn is an India-first career opportunity discovery product. The user explicitly requested removing Remotive, adding more India-focused event platforms, publishing the scraping bot privately on their GitHub account and providing a manual GitHub Actions trigger. They selected the Superpowers workflow and then selected **private JSON artifact plus local backend import**. Hosting, authentication and the existing Next.js/FastAPI/PostgreSQL modular monolith remain unchanged. No LocalStack or Docker setup is needed for this work.

GitHub CLI's account lookup returned `abhigyan6`. Proposed repository name (builder choice): `abhigyan6/alignn-scraper`, private. This document is not evidence that it has been created. No credentials or private account files may be read, printed, copied into the repository or requested in chat.

## Current implementation and change boundary

`apps/api/src/alignn/domains/opportunities/ingestion.py` currently schedules Remotive, Devfolio and three Greenhouse boards. The separate worker dispatches these jobs using the PostgreSQL queue. Devfolio crawls public catalog/detail pages with Scrapy and requires explicit India country data; Greenhouse filters internships to a curated set of Indian locations. Both upsert by source identity. The running website reads public opportunities from PostgreSQL; publishing a scraper artifact alone will not update it.

Current source collectors import application database/model modules, so they cannot simply be copied to GitHub Actions without also bringing database configuration. Extract a standalone `alignn_scraper` Python namespace alongside `alignn` under `apps/api/src`; it must never import `alignn`, SQLAlchemy, Clerk, application settings or any database adapter. Include that namespace in the API wheel. This preserves existing Docker/API build structure without a new local-path package dependency. Existing application source wrappers call the standalone collector, then perform application-owned persistence.

Source code in the app checkout is the maintained source; the private bot repository is a reproducible export of the standalone namespace, its focused tests, package metadata and workflows. Provide an explicit export/update procedure. Never create divergent hand-edited copies without recording which app commit they came from. The bot repository must not include `.env`, `.superpowers`, uploads, raw fetched pages, user fixtures, app Git history or cloud configuration.

## Approaches considered

1. **Private artifact and backend import — selected by the user.** Actions needs public internet access and its normal repository token only. A human downloads the JSON artifact and imports it locally through the backend CLI. This works while the app remains local and avoids granting the bot database access.
2. **Automatic delivery to deployed backend — deferred.** Requires a reachable backend and authenticated ingestion route/credential lifecycle. The app is currently being finished locally, and hosting changes were not requested here.

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

Reuse an identified user agent and robots handling. Proposed upper bounds: one active request per domain; at least one second between requests; 15-second request timeout; two MiB decompressed HTML per page; one retry; at most 100 detail pages per event platform; 180 seconds per source, with sources isolated into a bounded Actions matrix (maximum two source jobs concurrently, ten minutes per source job). The default all-source run explicitly reports the enabled/blocked source set. A report/merge job combines only validated source outputs. This avoids serial starvation as the source registry expands. No automatic schedule is enabled and no free-runner quota is assumed. Restrict redirects and prevent metadata/private-address fetches. Public outbound application URLs are validated and retained but never followed to submit applications.

Output is UTF-8 JSON with `schema_version: 1`, timezone-aware UTC `generated_at`, source reports and a normalized opportunity list. Each source report includes a fixed source key, status (`ok`, `partial`, `failed`, `empty`), successful check time, accepted/skipped/failed counts and generic error codes. Rows retain source name, stable source ID, canonical source/application URL, title, plain-text description, organizer/employer name when published, category, location, explicit country evidence, known work mode and actual registration/start/end timestamps. Use `null` for unknown timestamps; never convert event end dates to application deadlines. Inferred skills remain preferences; do not invent eligibility, stipends, verification or organizer endorsement.

Use the same normalization in Actions and local scheduled jobs. Deduplicate within each source using its stable ID/canonical URL. Do not merge similarly titled events across platforms without reliable shared identity. Do not emit participant objects, personal contact fields, profiles, images, full page state or raw HTML. Application/user data never enters the collector.

A partial source may contribute its individually validated rows, marked partial. Failed/empty source results must be visible in the report rather than silently appearing successful. Preserve diagnostics as error codes/counts, not raw responses. Nonzero exit when every requested source fails; a run with some failed sources is labeled degraded, with a valid artifact and explicit summary.

## Backend import and Remotive retirement

Add a backend-owned CLI, proposed `python -m alignn.domains.opportunities.import_scraped --file /path/to/opportunities.json`, with `--dry-run` support. Reads a local file only; never evaluates code or fetches supplied URLs. Use an explicit import allowlist and strict schema. Maximum artifact size ten MiB, maximum 1,000 records; reject unsupported versions, stale artifacts older than 24 hours, generation times over five minutes in the future, duplicate IDs, mismatched source reports, invalid country evidence, unsafe URLs and malformed dates before any writes. Invalid input must leave existing data unchanged.

Dry-run validates and reports counts without writes. Actual import occurs through the API's Python domain modules using a transaction, source lock, idempotent source identity and source-check ordering. Older per-source snapshots cannot overwrite newer data. Assign fresh ingestion time separately from original source check time where appropriate; never make old data appear freshly fetched. Re-importing identical data must not create duplicates or increment opportunity versions unnecessarily. Recompute inferred preferred skills from the existing local catalog before version comparison; changing deadlines increments deadline version. Leave organization verification false for feed-created organizations.

Public catalogs are often curated/partial: missing records do not establish closure. Close an imported record when its sourced deadline/end has passed or the source explicitly says it is closed/cancelled. Skip ended/closed events on new import. Imported source success must not reopen retired Remotive data.

Remove Remotive listings from discovery and search, including existing imported listings, not just future ingestion. Remove Remotive scheduling and network-fetch behavior. Drain queued historical `ingest_remotive` jobs as no-ops so old jobs cannot republish data. Retire existing Remotive rows by changing status to CLOSED and bumping version only when necessary; preserve opportunity IDs, saves and application history. Add a query exclusion as protection until all old workers are restarted. Do not delete those records or their linked user data. Update source/runbook documentation so Remotive is clearly retired rather than offered as an active command.

Scheduled local jobs continue to use the existing worker and PostgreSQL queue for the retained/new verified sources. The Actions workflow is manual and separate; both paths use equivalent normalization, not competing database rules.

## Private repository and manual Actions

Create the reviewed export as a private repository under `abhigyan6`. Verify repository privacy and the remote before pushing. No public publication, deployment or DNS changes. Record export origin/commit in the bot README.

Workflow `Scrape Indian opportunities` has `workflow_dispatch`, a choice input for `all` or an enabled source, a single workflow concurrency group and bounded per-source matrix jobs with ten-minute timeouts (maximum two concurrent source jobs). No automatic schedule initially. A source-specific manual choice runs only that enabled adapter; `all` runs the enabled registry and reports blocked/unverified targets separately. Runner: GitHub-hosted Ubuntu with Python 3.12. Pin reviewed action revisions, use `contents: read`, disable persisted checkout credentials, and install only the standalone bot's locked dependencies. Do not expose database ports or give database, AWS, Clerk or Heroku credentials to Actions.

Run fixture tests before scraping. Upload only `output/opportunities.json` plus a sanitized source report as a private Actions artifact, retained seven days; write source counts/status to the job summary. Never put untrusted source text in shell commands or interpret it as GitHub workflow output. A verification manual run is authorized by the requested functional workflow; check the account's Actions restrictions/availability, do not claim remaining free minutes or enable paid runners/billing.

Document the click path: repository -> Actions -> Scrape Indian opportunities -> Run workflow -> source -> Run -> download artifact -> backend dry-run -> backend import -> reload discovery. Closing the Mac does not prevent GitHub-hosted collection, but local import still requires the app database. The artifact is not an automatic live feed into Heroku or the website.

## What the manual button does, and does not do

The selected delivery flow is:

1. The user presses **Actions -> Scrape Indian opportunities -> Run workflow** in the private repository. GitHub's `workflow_dispatch` starts its hosted runner jobs; the laptop does not perform the collection.
2. The bot checks source access rules and fetches current public listings. It validates Indian relevance, source URLs, IDs and real dates, and produces per-source status reports.
3. The merge job produces the versioned JSON artifact and a sanitized summary. The user can download the artifact from that run while it remains retained. A green run is collection/export evidence, not website-update evidence.
4. On the Mac, the user downloads the artifact, runs the backend import with `--dry-run`, then imports it into the configured local PostgreSQL database.
5. The next discovery request reads the updated database. Existing unchanged records are preserved, new ones are inserted, changed ones are updated and expired/explicitly closed records are handled under the closure rules above. Match snapshots are recomputed through the existing worker where invalidated.

**Pressing the button alone will not update the website in the currently selected design.** It requires the backend import in step 4. GitHub cannot reach the Mac's `localhost`, and uploading an artifact is not a database write. Heroku's database is not automatically linked to the new bot repository.

For a future single-button website refresh, add an explicit authenticated handoff: either a deployed backend ingestion endpoint, or an app-side worker that polls/downloads approved private artifacts using narrowly scoped repository-read access. Both must call the same backend validator/importer. This would require a further design choice and runtime authentication configuration; it is not silently included in the user's previously selected manual-import approach. No database connection string goes into scraper source code. Report collected, exported, imported and visible states separately.

References: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow and https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts.

## Acceptance and verification

- Tests first for Remotive job retirement, exclusion, status update and preservation of saves/application history.
- Fixture tests for each platform's true geography, unknown/misordered/expired dates, source changes, malformed/duplicate IDs, partial responses and personal-field exclusion. Include at least one live successful future India event per new adapter; fixture success alone is insufficient.
- Standalone tests run without application modules, app configuration, database services or credentials.
- Real PostgreSQL import tests use only the dedicated test database and exercise dry-run, idempotency, freshness ordering, all-or-nothing validation, partial manifests, deadline versioning and expired/cancelled listing handling.
- Workflow syntax/config checks; verify private repository setting, default-branch workflow visibility, successful manual dispatch and a downloadable valid artifact. Treat blocked/failed upstream sources as failures rather than fabricated coverage.
- Import the verified artifact into the confirmed local app database, restart relevant background services, and check Indian discovery through the running API. No production import/deployment implied.

## Scope exclusions and open items

No event hosting, registrations, teams, judging, auto-applications, resume transmission, new auth flows, AI eligibility decisions or scraper dashboard. No new cloud infrastructure, LocalStack, database move or claim of complete India coverage.

Builder choices: source-specific parsing selectors, internal module names, fixture sanitization and export mechanics may be decided during the implementation plan, preserving these contracts. Unverified platform access is a source gate, not permission to bypass restrictions. Exact source substitution must be recorded if KonfHub fails its gate. Repository creation or an external Actions run blocked by account permissions must be reported accurately; source validation work can continue independently.
