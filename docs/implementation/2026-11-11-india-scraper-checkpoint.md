# Automatic India-first scraper checkpoint

11 November 2026. Active app branch `codex/audit-vercel-recovery`, active checkout `/Users/abhigyandwivedi/Developer/alignn-web`. No app deployment or main-branch push was performed.

## Verified delivery

Private [bot repository](https://github.com/abhigyan6/alignn-scraper), source export metadata `EXPORT.json`, numeric repo1453961313/workflow414656784. First all-source [manual run43022085421](https://github.com/abhigyan6/alignn-scraper/actions/runs/43022085421) succeeded. The local maintenance worker polled/downloaded/validated/applied it automatically; every source partition had an APPLIED receipt. The live local discovery API then returned13 Devfolio,13 Luma,4 HackIndia and1 Stripe internship;13 Remotive rows were CLOSED and11 past HackIndia observations skipped. Counts are dated observations.

Backend test database was the dedicated `alignn_audit_test` on localhost55439, never the app/user database. A separate local app migration was run only after checking its server address and excluding a test database. API readiness and web/DB/scanner/mail port checks passed after restart. Production credentials were not read, entered or changed.

## Independent review and regression fixes

One requested fresh reviewer was unavailable at its model usage limit before producing a review. The replacement fresh reviewer completed a read-only whole-change review. Important findings were reproduced RED, fixed, then verified GREEN:

| Finding | Regression / repair |
|---|---|
| Incomplete cached ATS snapshot could close later listings | `test_incomplete_ats_recheck_never_closes_another_listing`; cache only validated complete unique-ID snapshots. |
| Negated/conflicting India evidence accepted | `test_negative_or_conflicting_india_evidence_is_skipped`; conservative geography rejection. |
| Nullable/malformed JSON-LD could lose a partial result | `test_jsonld_null_and_nullable_metadata_are_controlled` and `test_malformed_detail_preserves_good_rows_as_partial`; typed parser boundaries. |
| All failed details reported partial/success | `test_all_detail_failures_are_failed_not_empty_partial`; no rows plus errors is FAILED. |
| Closed saved records inaccessible | `test_closed_saved_history_and_detail_are_readable_only_by_owner`; closed history remains readable only to its saver/applicant or authorized organization member, discovery remains active-only. |
| Fresh scheduler missed model metadata | `test_scheduler_registers_models_in_a_clean_process`; register domain tables before background ORM flushes. |
| DNS exceptions escaped source failure boundary | `test_dns_failure_is_a_controlled_source_failure`; controlled network error. |
| New poll jobs could bypass retry backoff; receipts/jobs unbounded | focused backoff/terminal-receipt/retention tests; durable poll backoff, receipt outcomes and bounded30-day/7-day cleanup. |

## Decisions and limits

- Existing feature checkout retained; no additional worktree due disk constraints. Review range is limited to this scraper change, not older branch work.
- Reviewed skill helpers lacked executable bits; bash/manual equivalent bookkeeping preserved test/ledger evidence without modifying installed skills.
- Source output bounded to100 rows/source, matching100 detail pages. Eight-source/80MiB uncompressed/85MiB ZIP caps replace the contradictory ten-MiB/1000-row contract. Byte-aware chunks preserve complete facts; larger catalogs need additional bounded runs.
- HTTPX and standard-library parsers reuse existing dependencies; no extra reactor/browser package, LocalStack, Redis or database service was installed. Existing legacy adapters remain a local fallback; production pull disables their discovery jobs.
- No automatic stale suppression policy was introduced; unavailable sources keep their true verification age and do not imply closure.
- Production hosting/authentication, Actions allowance and cron readiness were outside the review and remain operator gates; cost if skipped is failed delivery or unexpected usage. No new production deployment was authorized by this implementation checkpoint.
- Public access/robots does not establish legal permission; source terms/redistribution review remains before public launch, with risk of source withdrawal/restriction.
- Required blocked platforms remain disabled and documented; coverage is incomplete until permitted contracts are verified. Fabricated adapters would give misleading coverage.
- Capacity/SLO claims remain unverified beyond the small row-size sample; full matching growth needs representative measurements before launch.
- Legacy adapter duplication was not independently blocking because production discovery jobs are disabled when pull is active; future maintainers must keep that switch enforced.
- Reviewer mutation testing was not run because the final review was explicitly read-only; regression and integration tests provide the evidence used here.
- External vulnerability currency/action-release authenticity was not independently audited by the reviewer. Official action release commits were resolved through GitHub and pinned; dependencies are hash locked, but that is not a vulnerability-free claim.

## Remaining activation/source work

Unstop currently blocked; Hack2skill and KonfHub need verified public contracts. No complete-India-coverage claim. Production needs the privately configured repository-scoped Actions-read token, migrated database, supervised maintenance/collection workers and scheduler, a verified backup/restore procedure, monitoring/alert delivery and an allowance check before enabling cron. See [operations](../runbooks/india-scraper.md). Custom UI dashboard and other product work are outside this scraper checkpoint.
