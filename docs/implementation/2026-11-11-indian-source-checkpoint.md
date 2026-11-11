# Indian opportunity ingestion checkpoint

User requested research wrap-up and an implementation pause on 11 November 2026. Source changes are saved in local Git after resumed validation; not deployed.

## Already changed before the pause request

- Added Scrapy dependency and locked resolver output.
- Added `domains/opportunities/devfolio.py`: bounded public-page spider, strict canonical URL/identity checks, robots enabled, concurrency one, one-second request delay, 15-second requests, two-MiB page cap, 180-second crawl budget and 240-second child-process cap. Only normalized event fields survive; participant objects are omitted. Explicit country India required. Unknown eligibility remains unstructured.
- Added `greenhouse.py`: curated public GET adapters for Stripe, Figma and Razorpay; Indian internship selection, word-boundary checks, safe employer application URLs and complete-snapshot validation.
- Added six-hour scheduled jobs and job-handler routing. Long-running work has periodic lease renewal using independent short transactions.
- Added `UNKNOWN` work mode rather than inventing an internship's remote/onsite policy; regenerated OpenAPI/client and added readable discovery copy.
- Added source and worker regression tests.

## Verified at the checkpoint

- Live read-only Devfolio preview: 14 India events, zero detail parse failures in that run. These are a dated observation, not a fixed catalog size.
- Local app database import completed: 14 Devfolio hackathons and one Stripe internship; zero qualifying internships in the checked Figma/Razorpay snapshots. This does not establish UI verification or production deployment.
- Official public employer boards: all three returned HTTP 200; Stripe returned a Bengaluru internship, independently checked on its official careers page.
- 19 affected PostgreSQL integration tests passed, covering source parsing, country/identity checks, unknown dates, PII field exclusion, duplicate prevention, source failure preservation, complete-snapshot closure and worker lease renewal.
- Backend Ruff checks and API generation passed.
- Initial test invocation failed because the stopped temporary cluster restarted on its default port. Corrected to the dedicated 55439 test port before the passing run; app data was not used for tests.

## Resume work after the pause

1. Read `docs/reviews/2026-11-11-competitive-research.md` and inspect the current Git diff.
2. Read any completed `/tmp/alignn-ingestion-review.md` from the authorized CLI review, verify findings, and fix real defects before committing.
3. The local import completed successfully. Verify those records through the API before repeating a crawl. Confirm local DB via SQL server address, without printing runtime credentials. No production import/deployment is authorized by this checkpoint.
4. Run the full backend suite on the dedicated test database, web typecheck/build, formatting and lockfile vulnerability audit. The 19 affected tests are not a full release pass.
5. Verify source records through the actual local API and discovery/detail UI; restart worker/scheduler from the active checkout if needed. Schema additions require matching API/web revision.
6. Review source terms/redistribution expectations, source health visibility, expired-event handling and skills inference for employer listings before public rollout.
7. Commit reviewed source changes; implement the prioritized UX findings afterward. Resume extraction, additional categories and full product acceptance remain separate work.

The current local test cluster is `/tmp/alignn-recovery-pg.Lno8x6/data`, PostgreSQL port 55439, database `alignn_audit_test`. Never run truncating test fixtures on the app database. No credentials are included here.

## Resumed review and validation

Resumed on 11 November. Fixed repeat-sync version churn by computing inferred skills before comparison; added preferred-skill extraction to employer internships; moved Devfolio and Greenhouse network fetches outside write transactions with a locked freshness recheck; made busy source writes retryable; added transient heartbeat retries and support for both observed/string and possible list query keys. Malformed target internship snapshots still fail closed rather than silently deleting catalog records.

Validation: 91 backend tests passed on the dedicated PostgreSQL test database; Ruff, frontend typecheck, production build and Git whitespace checks passed. The local API required a restart to load the updated UNKNOWN work-mode contract. No production deployment performed. Further dependency audit and complete signed-in UI acceptance remain release tasks.

Antigravity review disposition: accepted version-churn, internship skill inference, long write transaction, transient heartbeat retry and busy-job findings. Retained failure-preserving snapshot behavior instead of its skip-malformed-record suggestion. The proposed heartbeat/finalization race is guarded by existing atomic status/token predicates, so no unguarded overwrite was established. Raw crawler stderr logging was rejected because page/provider details should not enter logs indiscriminately. List query-key support is defensive compatibility, not a claim that the observed source changed.

LocalStack recommendation: optional AWS service integration testing, especially private S3 file operations. Keep real PostgreSQL and existing local storage working. The GitHub Student plan is an emulator/testing benefit, not production hosting. No LocalStack account, licence, Docker service or cloud resource was configured in this checkpoint.

After restarting the local API, both category endpoints returned HTTP 200: one internship and 13 currently visible hackathons. The earlier import contained 14 hackathons; discovery excludes passed registration deadlines. Worker/scheduler restart and full browser acceptance remain pending.
