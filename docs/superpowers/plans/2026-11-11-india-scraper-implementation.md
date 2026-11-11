# India-first automatic collection implementation

> Execute inline using executing-plans. Approval: user's “sure go ahead”, 11 November 2026.

**Goal:** Private, manually triggerable collection with automatic backend delivery, explicit expiry and no database access from GitHub.
**Spec:** `docs/superpowers/specs/2026-11-11-india-scraper-design.md`; audit `docs/reviews/2026-11-11-india-scraper-workflow-audit.md`.
**Architecture:** Existing Next.js/FastAPI/PostgreSQL monolith and Python worker; independent collector namespace; no cloud deployment or additional paid services.

## Global constraints and resolved contracts

- Preserve saves/applications; retire Remotive rather than delete opportunities.
- Schema 1 bundle: UTF-8 manifest + byte-aware JSON chunks, each <=1 MiB, <=100 records; <=100 rows per source, <=8 sources, <=80 MiB total uncompressed, <=85 MiB ZIP, <=128 members, <=100:1 compression ratio. No extraction to disk. Descriptions <=20,000 characters; never truncate eligibility/deadline facts. Reject an individually oversized row explicitly. Manifest includes each chunk's SHA-256, size and source. Maximum envelope 256 KiB. These replace the inconsistent ten-MiB total cap.
- Invalid envelope rejects all before writes; independently validated source partitions commit atomically. Failed/empty reports do not imply missing rows closed. Every row has observed_at and source state; backend stores imported_at, content hash, closure reason and recheck metadata. Newer observations win; equal timestamp/conflicting hash rejects the entire partition.
- Receipt identity: repository/workflow/run/attempt/artifact/source; digest immutable; receipt and source writes commit together. Enumeration never acknowledges application. Retry pending receipts independently; job cap five then FAILED. Receipts retained >=30 days, exceeding replay window.
- Local recovery imports have a separate deterministic identity. Production requires pinned repo/workflow IDs/default branch and private Actions-read authentication; CLI auth allowed only in development without reading tokens. Activation is explicit; no implicit production deployment.
- Maintenance and collection worker lanes use the same queue with disjoint kinds. Read-time expiry works even if workers stop. Production must supervise both lanes. Source discovery only runs in GitHub when pull is enabled.
- Known-record rechecks: persisted next_check_at, <=20/source/cycle, minimum one second, non-overlap via database source lock; GitHub discovery <=100 pages/source/6h and local rechecks <=20/source/6h. No claim of cross-host global serialization. Failures remain unknown, never expired; no new 72h suppression policy without approval.
- Matching: preserve global ranking semantics, fetch profile evidence once per rebuild, exclude inactive candidates and prune inactive snapshots. Capacity measurement required before production; no fabricated load result.
- Scheduling remains gated off until production and Actions allowance are checked. Manual refreshes coalesce; running collection is not cancelled. Single-host downtime remains accepted.

### Task 1: Retire Remotive and enforce active discovery

**Files:** opportunity ingestion, service, shared visibility module; matching service; worker handlers; integration test_scraper_pipeline.py.
**Interfaces:** active_filters(now) -> SQL predicates; expire_opportunities(db, now) -> counts; legacy Remotive handler -> no-op.
1. Write PostgreSQL tests for ended events without cutoff, deadline boundary, Remotive retirement preserving saves, retired job drain and matching exclusion. Run focused tests: expect missing behavior failures.
2. Implement predicates/retirement/maintenance and remove scheduling/fetch behavior. Preserve old normalization helpers only where existing tests need compatibility; no runnable network source.
3. Run focused source/discovery/jobs regression tests. Expected: pass. Commit task.

### Task 2: Standalone collector and bounded artifact schema

**Files:** apps/api/src/alignn_scraper/{models,bundle,transport,registry,adapters,__main__}.py; standalone tests outside app conftest; API wheel metadata.
**Interfaces:** collect(source)->SourceResult; bundle bytes -> validated source partitions; static registry with enabled/blocked targets.
1. Write fixture tests for HackIndia, Luma, Devfolio and Greenhouse; India evidence, unknown dates, PII exclusion, source status, unsafe URLs, robots/redirect/size limits; chunk boundaries/Unicode/digest/ZIP validation. Expect imports to fail first.
2. Implement pure collectors and shared validators; only enable sources with verified public contracts. Verify at least two new platforms against public future India events; record unresolved required platforms explicitly.
3. Run standalone tests without app imports/database; live preview enabled sources; existing adapters delegate to shared normalization where feasible without breaking contracts. Expected: sanitized valid bundle; no fabricated coverage. Commit task.

### Task 3: Transactional importer, observations and receipts

**Files:** opportunity import_scraped.py, ingestion_models.py, migrations; integration test_scraper_pipeline.py.
**Interfaces:** validate_bundle(bytes)->partitions; apply_source(db, partition, identity, digest)->receipt; dry-run no writes.
1. Write PostgreSQL tests for schema rejection, per-source atomicity, replay/concurrent identity, ordering/conflict, cancellation/reopening/deadline extension, inferred skills/version stability and expiry preservation. Expect missing modules first.
2. Implement migration, receipt claim/advisory source lock, strict importer and CLI; network outside transactions. All rows validate before a source write; backend own OpportunityCreate validation remains authoritative.
3. Run dedicated PostgreSQL tests and migration upgrade. Expected: no duplicates/rollback on invalid source. Commit task.

### Task 4: Automatic pull, bounded rechecks and queue lanes

**Files:** GitHub sync module/settings; scheduler/worker/handlers; recheck module; integration/unit tests.
**Interfaces:** pinned GitHub metadata -> durable receipts/jobs; lane selection; source rechecks use stored canonical identity and observation fencing.
1. Write tests for untrusted workflow/run, redirect auth stripping, ZIP tampering, pagination/replay, retry/lease loss, maintenance isolation and recheck 404/410/429/extension semantics. Expect new behavior failures.
2. Implement polling, safe download, resumable receipts, startup catch-up, configuration kill switches, lane filters and bounded inventory cursor. No remote deployment. CLI-auth development mode consumes existing gh auth internally.
3. Run focused/full backend tests with dedicated test DB. Expected: pass and pending failures never block unrelated sources. Commit task.

### Task 5: Private reproducible export and GitHub Actions

**Files:** scripts/export-scraper.py; scraper metadata/workflow templates; private repo.
**Interfaces:** allowlisted export(origin SHA) -> standalone repo; source matrix -> bounded bundle artifact; workflow identity pinned by operator settings.
1. Test export allowlist/standalone independence and workflow contract. Review locked dependencies and pinned action revisions.
2. Export; verify correct private repository remote, create if missing, push requested standalone bot. Dispatch manually, inspect all source outcomes, download artifact without credential output.
3. Validate real artifact and import automatically using local worker; verify discovery via local API. Expected: receipts and real India listings, distinguish collection success from backend success. Commit task.

### Task 6: Review, operational handoff and capacity evidence

**Files:** runbook/source assessment/checkpoint; focused tests for any important review findings.
**Interfaces:** operator configuration/receipt summary/adapter kill switches; no secrets in docs or logs.
1. Record last collected/imported/verified timestamps, failure counts, startup/rollback/credential rotation steps and proposed alerts (12h source failure, 10min import lag, >20% malformed two runs). Record matching/catalog row-size evidence and production limits without claiming SLOs.
2. Fresh whole-change reviewer (required by executing-plans), assess strict parser/network boundaries and late writes after lease loss. Fix important findings with failing regression tests then full relevant suite.
3. Verify private bot and local automatic handoff; document blocked upstreams, disabled production schedule and remaining private production configuration. Preserve local branch, no app deployment/main push. Expected: evidence-bounded final handoff.

## Review focus

Untrusted HTML/JSON/date/country evidence; ZIP and redirects; GH owner/workflow/branch identity; source timestamps vs imported timestamps; concurrent retry and late writes; preservation of saved/history records; no private data/credentials in exported files; no platform represented as enabled before live verification.
