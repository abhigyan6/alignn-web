# India scraper workflow: system-design audit

Date: 11 November 2026. Reviewed design and code at `cfb347a`. This is a static design/code audit, not a live production security test, performance measurement or evidence that the proposed bot/importer is deployed. No application code, credentials or cloud resources were changed by this audit.

## Skill discovery and installation

Searched the active `.codex/skills` and `.agents/skills` roots, including symlinks; no `system-design` skill entry was found. Used the installed `find-skills` discovery guidance and reviewed catalog/source candidates. Selected `wondelai/skills@system-design`: Skills CLI reported approximately 6.6K installs; GitHub returned an MIT license and 2,667 repository stars at inspection. Popularity is selection evidence, not assurance of correctness. A less-established candidate was inspected but not installed.

Installed only `system-design` and its reference documents into `/Users/abhigyandwivedi/.codex/skills/system-design`, pinned to source commit `d8d5d75f83da9f16d8aad5bab5f5b341a4770a30`. The reviewed Codex skill-installer copies the selected directory; no candidate scripts, plugin hooks, services or telemetry were enabled. Skill version in the inspected manifest: 1.4.1. Source: https://github.com/wondelai/skills/tree/d8d5d75f83da9f16d8aad5bab5f5b341a4770a30/system-design . It will be discoverable in the next turn; its inspected system-design guidance was applied to this audit. Complementary installed `api-and-interface-design` guidance was applied to import contracts and idempotency.

## Verdict

**Keep the architectural direction, but close the high-priority contract/operations gaps before production implementation.** A standalone collector, private artifact handoff, backend-owned PostgreSQL writes and the existing worker/queue are proportionate. No Redis, Kafka, microservices or multi-region deployment is justified by the supplied workload evidence.

Good existing decisions: explicit India evidence; unknown deadlines remain unknown; Remotive retirement preserves saved/application history; public source failures do not erase the catalog; trusted repository/workflow checks; bounded fetching and artifact parsing; backend read-time expiry filtering; manual import recovery.

The ten findings below distinguish current code gaps from proposed-design gaps. Suggested repairs have not been applied to the design or application as part of this audit.

## Findings, in priority order

### F1 — P1: The worker cannot promise minute-level maintenance behind unbounded job delays

Evidence: design lines 83, 97–99; `jobs/worker.py:171–193` leases one job then dispatches synchronously, ordered by the existing queue's run time. Matching rebuilds and source checks can be long. A scheduler ticking once a minute only enqueues work; it does not establish that imports/expiry execute every minute.

Impact: ingestion, matching, mail and expiry can delay one another. The proposed 60-second poll is a scheduling target, not a user-visible freshness bound.

Repair: keep the same PostgreSQL queue and worker codebase, but classify slow source rechecks separately from short maintenance/import jobs. Add bounded job-kind selection/priority with fairness, or two supervised worker processes with disjoint kind filters only if measured memory/connection headroom permits. Run network fetches outside write transactions. Use deadline/end filters on public reads so expiry is enforced even when maintenance is late. Record oldest-due age; define a target for import latency after artifact availability, not just polling frequency.

Verification: a deliberately slow source job must not prevent the maintenance lane from enforcing due expiry. Test queue fairness and a lost lease; do not assume an extra process is free or highly available.

### F2 — P1: Import ledger, retry state and cursor rules are not yet a concrete contract

Evidence: design lines 63, 85–89 says persist outcomes, cursors and deduplication, but does not define durable identities or when a run is acknowledged.

Impact: advancing a cursor before commit can lose a run; replay after a crash can duplicate effects; taking only the latest completed run can miss another source's newer result. A retry budget exhausted once must not block every later run.

Repair: define a database receipt unique on `(repository_id, workflow_id, run_id, run_attempt, artifact_id, source_key)` with artifact digest and explicit states `DISCOVERED`, `IMPORTING`, `APPLIED`, `REJECTED`, `RETRYABLE`, `FAILED`. Claim work atomically. Store each source's apply receipt in the same transaction as its opportunity writes. Track enumeration separately from successful application; persist pending receipts before moving an enumeration watermark. Same identity/different digest is rejected. A later same-source artifact may supersede an older one only under an explicit source-time rule; do not discard unrelated-source work. Keep receipt/dedup records longer than the permitted artifact replay window.

Verification: crash after enumeration, before/after database commit, concurrent pollers, rerun of an Actions attempt, expired artifact, failed source followed by another source's success.

### F3 — P1: Source observation time and expiry/reopen ordering need explicit fields and fencing

Evidence: design lines 53, 63, 87, 103–107; current opportunity model has one `source_checked_at` plus row/deadline versions, not the proposed closure/recheck provenance.

Impact: using artifact generation/import time as observation time can make stale data look current. An old queued expiry check can close a deadline extension that committed meanwhile; an older open snapshot can undo a newer cancellation.

Repair: define per-record `observed_at`, backend `imported_at`, source-observed state (`OPEN`, `CLOSED`, `CANCELLED`, `UNKNOWN`), closure reason and provenance. Keep deadline expiry distinct from source cancellation. Apply source observations in a single ordered rule under a row lock or compare-and-swap on the expected source revision. An expiry job reevaluates the current stored deadline after locking; it never acts on only the job's old payload. Older observations are no-ops. Equal observation time with conflicting content is quarantined/rejected, never arbitrarily last-writer-wins. Treat source timestamps as untrusted schema data and validate future bounds.

Verification: deadline extension racing expiry, cancellation followed by an older open artifact, out-of-order all/source-specific runs, equal timestamps/conflicting hashes, legitimately newer reopening.

### F4 — P1: Partial success versus atomic rejection is contradictory without a transaction boundary

Evidence: design lines 57 and 87 allow partial-source import, while line 61 says malformed/invalid input causes no writes. Both can be reasonable, but the unit of atomicity is undefined.

Impact: one malformed platform payload could prevent every valid platform from updating, or an importer might accidentally commit some unvalidated rows before rejecting the artifact.

Repair: reject an invalid envelope, untrusted provenance or unsafe ZIP before all database writes. Validate every row in a selected source partition before that partition's transaction. Allow independent valid partitions to commit with independent receipts; reject the entire malformed partition without modifying that source. `partial` must mean a bounded/known incomplete crawl whose emitted rows all validate, not permission to ignore malformed emitted records. The combined run reports the rejected partition as degraded.

Verification: one malicious source partition among valid ones, unknown source keys, mismatched counts, malformed schema and partial crawl with individually valid rows.

### F5 — P1: Artifact byte limits do not fit the maximum logical record count

Evidence: design line 61 permits 1,000 records within ten MiB. Existing `OpportunityCreate.description` permits 20,000 characters. One thousand 20,000-byte ASCII descriptions already exceed 19 MiB before other fields; UTF-8 content can be larger.

Impact: a legitimate successful scrape can produce an artifact that the importer must reject. Compression does not solve the uncompressed validation limit.

Repair: specify byte-aware chunking and a manifest, for example bounded per-source chunks with their own digests and sizes. Keep the ten-MiB uncompressed envelope policy only if chunks are independently downloadable/validatable; otherwise reconcile the entire artifact and record-size caps explicitly. Never silently truncate registration/eligibility facts to force acceptance. Bound compressed download size, total decompressed size, member count and compression ratio before parsing; read an allowed JSON member directly rather than extracting arbitrary paths.

Verification: maximum-length ASCII and multibyte descriptions, a source crossing a chunk boundary, a missing/repeated chunk and a ZIP bomb. Exact chunk sizing belongs in the revised contract before implementation.

### F6 — P1: Current discovery does not enforce known event-end expiry

Evidence: `domains/opportunities/service.py:63–71` filters status/mode and future-or-null registration deadline, but not `ends_at`. The proposed design requires end-date filtering at line 99. The scheduler currently registers ingestion/retention only (`jobs/scheduler.py:9`).

Impact: a published event with no registration cutoff and an elapsed end can remain discoverable until another action closes it. This is a current source-code gap, not a verified live production incident.

Repair: use a shared active-opportunity predicate that excludes elapsed event ends as well as elapsed registration cutoffs. Apply it to discovery and match candidate selection; preserve closed detail/history access. Add bounded expiry maintenance. Do not infer expiry from a start date alone. These changes require regression tests and source-state rules from F3.

Verification: exact deadline/end boundaries in aware UTC timestamps, unknown cutoff + elapsed end, ongoing event with unknown cutoff, and saved/application-history preservation.

### F7 — P1: Expanded ingestion can amplify matching storage and rebuild cost

Evidence: `domains/matching/service.py:rebuild_matches` loops every PUBLISHED external opportunity for each user and stores a `MatchSnapshot`. The row includes JSON evidence. `opportunities/service.py` uses whole-catalog version information when queuing reranking.

Impact: scaling the source catalog also scales profile/opportunity combinations. Feed storage alone is not a useful database capacity estimate. Frequent source changes can invalidate broad ranking work, and duplicate cross-platform events can consume several candidate slots.

Repair: measure row/index sizes and representative rebuild duration before launch. Cache each user's profile/skill/project evidence once per rebuild; update only affected opportunity/user pairs where possible. Prune obsolete match snapshots under a defined retention rule. If a bounded candidate shortlist is introduced, explicitly revise global ranking semantics and tests rather than silently ranking only a page. Keep exact identity dedup separate from fuzzy duplicate suggestions; never merge solely by title. No sharding or Redis is justified yet.

Verification: a representative synthetic catalog and user dataset, unchanged sync causing no version churn, changed single listing, user-profile change, stale snapshot cleanup and preservation of ranking semantics.

### F8 — P2: GitHub artifact download security needs redirect and credential rules

Evidence: design lines 83–85 has sound repository/branch/workflow pinning and ZIP checks, but does not specify the download handoff. GitHub's artifact download endpoint returns a 302 to an expiring download URL (official reference below).

Impact: blindly trusting supplied download URLs or forwarding an Authorization header across redirects can disclose repository access. Persisting a signed download link makes retries fail after it expires.

Repair: construct the GitHub API URL from pinned repository/verified numeric artifact IDs. Authenticate only to the intended API origin. Validate the redirect scheme/host against the approved GitHub artifact delivery mechanism and download without forwarding the API Authorization header; never log the signed URL. Request a fresh download location on retry. Reject unknown/missing digests according to an explicit policy; a digest protects transport/content integrity, not the trustworthiness of the source data. Handle token expiry/rotation as an actionable operator error.

Verification: redirect to loopback/unapproved host, redirect credential forwarding, expired signed URL, wrong artifact owner/workflow, tampered digest and expired repository-read access. No credential values were inspected in this audit.

### F9 — P2: Two collectors and sparse observations can violate source budgets and prolong stale data

Evidence: design lines 51 and 97 put collection in Actions and active-listing rechecks in the production worker, with per-collector limits but no aggregate budget or guaranteed inventory coverage.

Impact: these processes can hit the same platform simultaneously. A capped run may repeatedly examine the first pages and starve older records. A stale retained record with no known deadline may stay visible indefinitely after persistent failures.

Repair: define per-source aggregate request budgets, `next_check_at`, persisted round-robin inventory cursors, `last_attempt_at` and `last_success_at`. Allocate discovery/recheck budgets deliberately; avoid overlapping full passes and honor Retry-After with bounded exponential backoff/jitter. Distinguish failed checks from successful source absence. Define a proposed staleness policy, e.g. show a stale warning after 24 hours and suppress unverifiable active discovery after 72 hours while preserving history; these durations need user approval, and suppression must not be labeled confirmed expiry. Do not claim a single source-wide concurrency guarantee without coordination across hosts.

Verification: more due records than a run budget, repeated 429/403, robots rule changes, interrupted recheck cursor and recovery after prolonged source outage.

### F10 — P2: Monitoring, cost ceilings and release recovery are not an actionable operating plan

Evidence: design lines 51, 75, 87–91 report statuses and acknowledge limits, but contain no alerts, workflow/import acknowledgement surface, concrete polling/backoff policy, deployment compatibility gate or restore drill. Existing process/readiness endpoints do not prove the poller is importing.

Repair: keep distinct per-source last-collected, last-imported and last-verified timestamps, oldest due job age and closure/parse/error counts. Produce a backend import receipt with added/updated/expired/unchanged/rejected counts; GitHub's green status means collection/export only unless a separate acknowledgement is configured. Proposed alerts: no successful required-source import for 12 hours; oldest import job due over 10 minutes; malformed/failing source ratio above 20% for two runs; heartbeat/credential failure. Thresholds are acceptance proposals, not measurements.

Keep 60-second metadata polling if needed for the button's response, with conditional requests and no repeated artifact downloads when nothing changed; back off on rate limits. Validate source-run/setup minutes against the account allowance before enabling cron; cap artifacts and retain only seven days. Version the artifact schema, approve collector commits/releases and test old/new importer compatibility before enabling a new collector export. Disable import or a broken adapter independently and retain the last good dataset; do not roll back user saves/applications to undo a bad catalog import. Document database backups/restore ownership and the single-host availability tradeoff.

Verification: collector succeeds but importer is offline, outdated schema, exhausted Actions allowance, token revoked, bad adapter rollback, failed migration and catch-up after more than the 24-hour import window. GitHub concurrency is not a durable FIFO queue; document whether repeated manual refreshes coalesce or must all run.

## Capacity and freshness estimates — assumptions, not measurements

A small planning scenario, not observed traffic:

- 1,000 daily active students × 20 API reads/day / 86,400 ≈ 0.23 average requests/second; a 10× assumed burst is about 2.3 requests/second. This does not establish latency under a particular host/DB plan.
- 5,000 catalog rows × an assumed six KiB normalized record ≈ 29 MiB before PostgreSQL/index overhead.
- 1,000 users × 5,000 match snapshots × an assumed 500 bytes ≈ 2.5 GB decimal (2.3 GiB) before index/tuple overhead. Actual rows must be measured; this scenario alone exceeds a one-GiB budget.
- Eight enabled source jobs × four scheduled runs/day × 30 days = 960 source-job executions/month. At an illustrative three minutes each: 2,880 runner-minutes, before setup/tests/report jobs. At the stated ten-minute job timeout upper bound: 9,600 source-job minutes. Two-way parallelism reduces elapsed time, not aggregate runner-minutes. No current quota/price was verified here.
- A one-minute poll is 1,440 metadata requests/day per poller before pagination and other API calls. Download only new artifacts; use conditional requests/backoff and check rate-limit headers.
- Freshness is `schedule delay + runner queue + crawl + artifact publication + poll delay + local queue + import + client refetch`. A 60-second poll cannot establish one-minute end-to-end freshness or the truth of every upstream deadline. Define and test an import-lag target after artifact availability separately from upstream data age.

## Skill checklist and proportionality

The installed skill mandates an eight-row diagnostic. Strict documentation-completeness score: **3/10 (2 of 8 rows fully explicit, rounded)**. This is a heuristic checklist score, not a measured reliability/security grade. Functional/non-functional constraints and queued asynchronous work pass. Remaining rows:

| Diagnostic row | Gap / proportionate action |
| --- | --- |
| QPS/storage estimate | Missing in the design; use the assumptions above and measure actual row/job sizes. |
| Every component redundant | Single host/worker/database/GitHub dependency are not redundant. Accept and document initial downtime risk, supervise/restart and rehearse restore; do not buy multi-region hosting to improve a score. |
| Database scaling strategy | Start with query/index/matching-state measurements and bounded retention, then scale vertically if needed. |
| Read-path cache | No explicit cache policy. Deliberately use uncached personalized reads initially; define version/invalidation if public caching is added. No automatic Redis installation. |
| Monitoring/alerts | Counts exist as intentions, but thresholds, acknowledgement and ownership need F10. |
| Deployment strategy | Add schema compatibility, migrations, adapter disable/rollback and recovery gates before production activation. |

The skill's generic redundancy/cache suggestions do not override the user's storage/cost constraints. The modular monolith remains appropriate; fixing contracts and operations matters more than adding components.

## Recommended build sequence

1. Finalize the observation/import schema, receipt identities, partial-success boundary, chunking and failure semantics (F2–F5, F8).
2. Retire Remotive with history preserved, implement read-time expiry and test it against PostgreSQL (F3/F6).
3. Implement verified source adapters and export them reproducibly; report blocked platforms honestly.
4. Add private manual Actions collection and prove a downloadable artifact using fixture tests and actual permitted sources.
5. Prove local import, then add automatic production pull, queue isolation and catch-up (F1/F2/F9).
6. Measure matching/catalog size, add receipts/alerts and establish production credentials/rollback before enabling scheduled runs (F7/F10).

## References and limits

- Skill source: https://github.com/wondelai/skills/tree/d8d5d75f83da9f16d8aad5bab5f5b341a4770a30/system-design
- Private artifact read permissions and expiring download redirect: https://docs.github.com/en/rest/actions/artifacts
- Cron timing limitations: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- Concurrency pending/queue semantics: https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency

Reviewed the full latest design and representative queue, scheduling, discovery, matching and opportunity models. No new importer, bot repository, new adapters or workflow was implemented or verified by this audit. Suggested policy durations/capacities remain proposals. Upstream source permissions/access still need platform-by-platform verification. No credential values, cloud resource state, production backups, remaining free minutes or live latency were inspected.
