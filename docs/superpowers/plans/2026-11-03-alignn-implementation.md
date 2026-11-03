# Alignn Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Execution method is pending the user's choice; do not infer authorization to delegate from this header.

**Goal:** Deliver a working Alignn full web application for discovery, external applications and free hosted individual or team events, with submission rounds, manual judging and results.

**Architecture:** One repository holds a Next.js frontend, a FastAPI modular backend and a separately running Python worker. PostgreSQL owns transactional state and durable jobs; private S3-compatible storage holds uploaded documents. The frontend consumes a generated OpenAPI client.

**Tech Stack:** TypeScript, React and Next.js; Python 3.12 or newer, FastAPI, Pydantic, SQLAlchemy, Alembic and PostgreSQL 18; pytest and Playwright. Select supported dependency versions against official documentation at implementation time and commit lockfiles. Use npm workspaces and uv for repeatable JavaScript and Python installs.

**Spec:** `docs/superpowers/specs/2026-11-03-alignn-design.md`.

## Global Constraints

- "Public signup creates a participant account only."
- "Default absolute lifetime is seven days and idle expiry is 24 hours."
- "Use UUID primary keys, timezone-aware timestamps, foreign keys, check constraints and database uniqueness."
- "API idempotency keys are scoped by actor and operation, store a request hash and response, and expire after 24 hours."
- "A scheduler sweeps due reminders every minute"; jobs have "up to five attempts" and a "10 seconds" external timeout.
- "Resume limit is 10 MB for PDF or DOCX"; submissions allow "PDF, PPTX, ZIP or a project link up to 25 MB".
- "Bound page size to 100." All personal API responses are private and uncached.
- "Sort eligibility and match across the candidate result set before pagination."
- "AI may explain structured evidence but cannot decide eligibility, moderation, scores or winners."
- "All screens, API operations, fixtures and documentation use Alignn branding."
- "No existing-user database migration is assumed for this fresh build."
- Every implementation milestone must run as a coherent working app; paid infrastructure and public deployment remain outside execution authorization.

## Review Focus

1. The browser sends a forged role, tenant ID or registration status: server-owned authority must ignore or reject it. Tasks 1, 3 and 5 test this.
2. A client retries after a timeout while another client takes the last place: return one durable result and never overbook. Task 5 tests duplicate and competing requests.
3. A user's profile or an organizer's deadline changes during an active event: preserve historical admission and explicit deadline versions. Tasks 4, 5 and 6 test this.
4. A worker crashes after an external side effect: recover its lease, retain in-app uniqueness and expose uncertain email delivery. Tasks 2 and 8 test this.
5. A small screen, keyboard-only user or disabled AI adapter encounters a critical flow: allow completion with accessible controls and deterministic facts. Tasks 7, 9 and 10 test this.

## File and interface map

| Path | Responsibility |
|---|---|
| `apps/api/src/alignn/main.py`, `config.py`, `db.py`, `errors.py` | App composition, validated settings, transaction access and public errors |
| `apps/api/src/alignn/domains/<domain>/{models,schemas,service,router}.py` | Domain records, contracts, transaction-owned behavior and HTTP boundary |
| `apps/api/src/alignn/jobs/{models,worker,scheduler,handlers}.py` | PostgreSQL leases, retry policy and side effects |
| `apps/api/src/alignn/adapters/{mail,objects,scanner,ai}.py` | Explicitly configured external capabilities and local adapters |
| `apps/api/migrations/versions/` | Ordered Alembic schema migrations; no startup schema creation |
| `apps/api/tests/{conftest,unit,integration}/` | Real PostgreSQL fixtures, pure domain checks and HTTP/concurrency tests |
| `apps/web/src/app/` | Public, participant, organizer and admin route groups |
| `apps/web/src/components/{ui,brand,opportunities,events}/` | Accessible primitives and reusable branded components |
| `apps/web/src/lib/{api,session,format}.ts` | Generated client integration, server session forwarding and date formatting |
| `packages/api-client/`, `packages/design-tokens/` | Versioned OpenAPI output and semantic CSS variables |
| `infra/compose.yaml`, `infra/Caddyfile` | Local PostgreSQL, private object storage, scanner, mail inbox and same-origin proxy |
| `.github/workflows/ci.yml`, `docs/runbooks/` | Reproducible verification, restore and failure recovery instructions |

API schema objects below live in their owning domain's `schemas.py`. Service functions accept a SQLAlchemy `Session`; public mutations run in one outer transaction and repositories never commit independently. A `DomainError(code, message, status_code)` maps to the shared error contract. UUIDs are UUID objects internally and strings at the HTTP boundary. `Actor` contains a user ID and current verified/administrative state, loaded from the database rather than client claims.

Test infrastructure defines `client: TestClient`, `db: Session`, an injectable `Clock.now() -> datetime`, and factories `make_user(verified=False, admin=False)`, `make_organization(owner_id, verified=False)` and `make_opportunity(organization_id, **overrides)`. Concurrency tests use independent PostgreSQL connections and committed fixtures, not one rollback-wrapped shared session.

## Milestone 1 Working identity and application foundation

### Task 1 Identity contracts and a runnable API

**Files:** Create root workspace configuration and `.env.example`; `apps/api/pyproject.toml`; API composition files; `domains/identity/{models,schemas,service,router}.py`; `migrations/`; `tests/conftest.py`; `tests/integration/test_identity.py`; `infra/{compose.yaml,Caddyfile}`; `.github/workflows/ci.yml`.

**Interfaces:** Produce `create_app(settings: Settings) -> FastAPI`, `Actor`, `get_actor(request: Request, db: Session) -> Actor`, `require_verified(actor: Actor) -> Actor`, `issue_session(db, user_id: UUID, now: datetime) -> SessionSecret`, `authenticate_session(db, token: str, now: datetime) -> Actor`. `SessionSecret` contains the plaintext cookie token and CSRF secret only for issuance; database records store hashes.

- [ ] Write `test_public_signup_cannot_create_admin`, `test_session_absolute_and_idle_expiry`, `test_logout_revokes_session`, `test_password_reset_single_use`, `test_cross_origin_mutation_rejected` and `test_disabled_user_session_rejected`. Assert forged ADMIN signup is 422, no administrator is inserted, expiry at seven days or 24 idle hours rejects access, reused reset tokens fail, and mutation without Origin/CSRF is denied.

```python
def test_public_signup_cannot_create_admin(client):
    response = client.post('/api/v1/auth/signup', json={
        'email': 'participant@alignn.test', 'password': 'Valid-long-password-42!',
        'full_name': 'Test Participant', 'role': 'ADMIN',
    })
    assert response.status_code == 422
```
- [ ] Run `uv run --project apps/api pytest apps/api/tests/integration/test_identity.py -q`; confirm the unimplemented behaviors fail.
- [ ] Implement participant-only signup, Argon2id hashing, normalized unique email, verified identity, opaque sessions and password reset. Before login, issue a short-lived anonymous CSRF session through `GET /api/v1/auth/csrf`; exchange it for the authenticated session on success. Use same-origin checks, CSRF verification and database-backed rate limits; clear both session and CSRF cookies on logout. No production secret fallback. Add health/readiness and release-time Alembic migration commands.
- [ ] Run the identity suite against PostgreSQL and migrate an empty database from the repository root with `uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head`. Set the migration script location relative to the config file. CI must fail if the test database is absent; do not fall back to SQLite.
- [ ] Commit `feat: establish Alignn identity and PostgreSQL foundation` with startup and test instructions.

### Task 2 Durable jobs and local delivery adapters

**Files:** Create `jobs/{models,worker,scheduler,handlers}.py`, `adapters/mail.py`, `tests/integration/test_jobs.py`, and the outbox migration. Update identity mail delivery to enqueue transactionally.

**Interfaces:** Produce `enqueue_job(db, *, kind: str, key: str, payload: dict, run_at: datetime, expires_at: datetime | None) -> UUID`, `lease_jobs(db, *, worker_id: str, now: datetime, limit: int) -> list[JobLease]`, `process_lease(lease: JobLease, adapters: Adapters, clock: Clock) -> None`. `JobLease` includes job ID, lease token, attempt count and payload. Later tasks register handlers by kind.

- [ ] Write `test_rolled_back_signup_has_no_mail_job`, `test_two_workers_do_not_share_a_lease`, `test_expired_lease_can_be_reclaimed`, `test_permanent_failure_is_terminal` and `test_retry_exhaustion_is_visible`. Assert rollback leaves zero jobs; an expired lease is reclaimable; stale lease tokens cannot mark a reclaimed job complete; attempt five becomes failed.

```python
def test_rolled_back_signup_has_no_mail_job(db, clock):
    from sqlalchemy import select, func
    from alignn.jobs.models import Job
    from alignn.jobs.worker import enqueue_job
    enqueue_job(db, kind='mail', key='rollback-case', payload={},
                run_at=clock.now(), expires_at=None)
    db.rollback()
    assert db.scalar(select(func.count()).select_from(Job)) == 0
```
- [ ] Run `uv run --project apps/api pytest apps/api/tests/integration/test_jobs.py -q` and verify initial failures.
- [ ] Implement SKIP LOCKED leasing, fencing by lease token, heartbeat, ten-second external timeout, jittered backoff and a maximum of five attempts within 24 hours. Use a local mail inbox and explicit disabled adapters when unconfigured. Mark stale or expired reminders skipped before any send. Add operator listing and audit-backed replay interfaces behind administrator access.
- [ ] Run identity and job suites; verify a local verification email reaches the local inbox and a worker restart recovers a committed job.
- [ ] Commit `feat: add durable background jobs and mail delivery`.

## Milestone 2 Discovery and external application flow

### Task 3 Profiles organizations and private files

**Files:** Create `domains/{profiles,organizations,files}/` modules, object and scanner adapters, migrations, `tests/integration/test_profiles.py`, `test_organizations.py`, `test_private_files.py`.

**Interfaces:** Produce `update_profile(db, actor: Actor, data: ProfileUpdate) -> ProfileOut`, `require_membership(db, actor, organization_id: UUID, capability: str) -> Membership`, `authorize_file(db, actor, file_id: UUID, purpose: str) -> FileGrant`, `verify_upload(db, file_id: UUID, adapters: Adapters) -> ScanResult`. File grants expire after five minutes; finalized metadata requires checksum and actual size.

- [ ] Write tests asserting cross-organization reads and writes are denied, an organization cannot publish before verification, the final owner cannot leave, invitations expire after 72 hours, and public teammate search excludes non-opted-in users and private fields.
- [ ] Write tests for blocked unscanned and failed objects, disguised extensions, 10 MB resume and 25 MB submission limits, unauthorized signed URL requests and revoked resume grants. Run the three new test files and verify the missing behavior fails.

```python
def test_anonymous_profile_is_private(client):
    assert client.get('/api/v1/me/profile').status_code == 401
```
- [ ] Implement canonical skills and aliases, bounded decimal grades with explicit 4/10 scale, profile revisions, organization invitations and operator verification. Implement quarantined signed uploads, actual-type checks and a configured malware scanner; scanning failure must leave the file unusable. Never execute or extract submitted code. Add optional per-event contact and resume grants without making them admission requirements.
- [ ] Run those tests and demonstrate verified upload/download locally. Verify organizer export projections omit email and resumes without the corresponding grants.
- [ ] Commit `feat: add profiles organizations and private document access`.

### Task 4 Publication eligibility matching and external tracking

**Files:** Create `domains/{opportunities,eligibility,matching,applications}/` modules, `tests/unit/test_eligibility.py`, `test_matching.py`, `tests/integration/test_discovery.py`, `test_applications.py`, and search/rule migrations.

**Interfaces:** Produce `evaluate(profile: ProfileEvidence, rules: EligibilityPolicy) -> EligibilityResult`, `calculate_fit(profile: ProfileEvidence, opportunity: MatchEvidence) -> FitResult`, `search_opportunities(db, actor: Actor | None, query: SearchQuery) -> OpportunityPage`, `record_application_event(db, actor, application_id: UUID, data: ApplicationEventCreate) -> ApplicationOut`. Result schemas carry algorithm and policy versions; `OpportunityPage` carries ranking status and next cursor.

- [ ] Write tests asserting missing required degree or branch returns INCOMPLETE, unsupported GPA scales never convert silently, aliases match by canonical IDs, hard constraints use AND and allowed values use OR. Assert a rule-free opportunity admits verified users.

```python
def test_missing_mandatory_degree_is_incomplete():
    from alignn.domains.eligibility.schemas import ProfileEvidence, EligibilityPolicy
    from alignn.domains.eligibility.service import evaluate
    result = evaluate(ProfileEvidence(verified=True, degree_id=None),
                      EligibilityPolicy(degree_ids=['btech']))
    assert result.status == 'INCOMPLETE'
    assert not result.can_register
```
- [ ] Write matching tests: all factor scores 100 yields 100; technical-only 100 yields 35; required skills weigh twice preferred; missing factors remain zero. Write discovery tests asserting drafts and unpublished results remain private, page size is capped at 100, and profile edits mark persisted ranking stale rather than sorting one fetched page as globally ranked. Write application tests proving one user cannot alter another user's tracker or organizer results.
- [ ] Run those test files and verify failures. Implement publication workflow, PostgreSQL full-text indexes, explicit HOSTED/EXTERNAL modes, saved opportunities and append-only external tracking. Implement matching weights 35/25/20/10/10 with deterministic token overlap and versioned worker snapshots. A pending rank request returns labeled chronological results. Lock opportunity policy edits after the first registration through Task 5's shared mutation service.
- [ ] Run pure and PostgreSQL suites. Export `packages/api-client/openapi.json`, generate TypeScript types and commit a repeatable generation command.
- [ ] Commit `feat: add opportunity discovery and explainable career tracking`.

### Task 5 Teams and transactional registration

**Files:** Create `domains/{teams,participation}/` modules and migrations; `tests/integration/test_teams.py`, `test_registration.py`, `test_registration_races.py`. Update opportunity mutation rules from Task 4.

**Interfaces:** Produce `register(db, actor: Actor, opportunity_id: UUID, data: RegistrationCreate, idempotency_key: str, clock: Clock) -> RegistrationOut`, `withdraw(db, actor, registration_id: UUID, clock: Clock) -> RegistrationOut`, `mutate_opportunity(db, actor, opportunity_id: UUID, expected_version: int, data: OpportunityMutation) -> OpportunityOut`. `RegistrationCreate` contains optional team ID and consent grants, never caller-chosen status or roster.

- [ ] Write tests asserting one participant occupies one active registration per event; a captain cannot register pending invitees; all roster members meet eligibility; registration freezes membership and policy; changed idempotency payload returns 409; the same request returns the same ID; a profile change does not retroactively alter admission.
- [ ] Write `test_last_seat_race` with 100 independent requests and capacity one; assert one confirmed registration and capacity count one. Test concurrent team invitations and registration, withdrawal before and after close, duplicate attempts after key expiry, capacity reduction and early deadline changes after registration starts. Run the new files and verify failures.

```python
# In test_last_seat_race, collect HTTP responses from independent verified users.
assert sum(response.status_code == 201 for response in responses) == 1
assert sum(response.status_code == 409 for response in responses) == 99
assert confirmed_registration_count == 1
assert opportunity_capacity_used == 1
```
- [ ] Implement opportunity-then-team lock ordering for all membership and registration mutations, immutable participant snapshots and database uniqueness. Track active participation separately from immutable historical roster rows so withdrawal can release a place before close without deleting history. Freeze mode and eligibility once any registration exists. Use server time after locks are acquired; persist the idempotency response, state and outbox in one transaction.
- [ ] Run race tests repeatedly only while resolving failures; then run the relevant full integration suite once. Verify exactly one notification job per registration.
- [ ] Commit `feat: add teams and safe hosted-event registration`.

## Milestone 3 A complete hosted event

### Task 6 Submission rounds manual evaluation and results

**Files:** Create `domains/{submissions,evaluations}/` modules and migrations; `tests/integration/test_submissions.py`, `test_evaluations.py`, `test_result_privacy.py`.

**Interfaces:** Produce `finalize_submission(db, actor, round_id: UUID, revision_id: UUID, key: str, clock: Clock) -> SubmissionOut`, `finalize_scorecard(db, actor, assignment_id: UUID, scores: list[CriterionScore]) -> ScorecardOut`, `publish_results(db, actor, opportunity_id: UUID, expected_version: int, decisions: list[ResultDecision], reason: str) -> ResultVersionOut`.

- [ ] Write tests for captain-only submission, safe-file or HTTPS-link requirement, draft-versus-final distinction, cutoff boundary, cancellation, round advancement, and immutable revision history. Define deadline acceptance by an atomic database finalization check after locks; document this precise server acceptance instant rather than promising a client-visible commit timestamp.
- [ ] Write tests asserting a 50%-weighted criterion scored 8/10 and a 50%-weighted criterion scored 3/5 yield 70; two reviewer totals 70 and 90 average to 80; incomplete active assignments block publication; tied advancement requires an explicit decision and reason; a reviewer cannot see another assignment or participant resumes. Assert unpublished results are inaccessible and corrections create a new audited version. Run these files to observe failures.

```python
# In scorecard integration tests, call finalize_scorecard with the values above.
assert first_scorecard.total == 70
assert published_result.mean_score == 80
assert incomplete_publication_response.status_code == 409
assert anonymous_unpublished_result_response.status_code == 404
```
- [ ] Implement ordered rounds, accepted-roster access, immutable revisions, normalized rubric weights, finalization locks and organizer-controlled advancement. Freeze rubric weights after the first finalized scorecard. Publish a result version transactionally with notification jobs; never accept a participant-supplied score.
- [ ] Run the submission/evaluation suites and demonstrate one local hosted event through registration, submission, scoring, advancement and publication using the API.
- [ ] Commit `feat: deliver submission rounds and versioned event results`.

### Task 7 Branded web application and generated client

**Files:** Create `apps/web/` package and config; `packages/design-tokens/{tokens.css,README.md}`; `packages/api-client/{src/index.ts,openapi.json}`; `apps/web/src/components/`; route groups `(public)`, `(auth)`, `(participant)`, `(organizer)` and `(admin)`; `apps/web/tests/e2e/{identity,discovery,participation,organizer}.spec.ts`.

**Interfaces:** Produce `apiRequest<T>(path: string, options?: RequestOptions) -> Promise<T>` using generated contracts and same-origin session cookies; server calls forward only the session cookie. Expose reusable `Button`, `Input`, `Dialog`, `Combobox`, `OpportunityCard`, `Deadline` and `RegistrationSummary` components with typed props. Use tested accessible primitives for complex controls rather than inventing their keyboard behavior.

- [ ] Before implementation, load the approved frontend skills and inspect the marketplace concept as a reference. Define semantic light/dark surface, text, border, focus and state tokens; a four-pixel spacing base; 16-pixel body text; 1.25 type scale. Verify font licenses and load fonts locally. Produce a reviewed vector variation of the Alignn mark with a documented distinction from the raster reference.
- [ ] Write Playwright flows for signup and verification through the local inbox, profile completion, search/save/external tracking, team invitation/acceptance/registration, submission finalization and organizer publication. Assert external Apply and hosted Register are distinct, drafts/results respect permissions and a registration failure never displays success. Run them against the unimplemented web routes to confirm failures.

```typescript
test('participant can open discovery', async ({ page }) => {
  await page.goto('/explore');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Find your people');
  await expect(page.getByRole('searchbox', { name: 'Search opportunities' })).toBeVisible();
});
```
- [ ] Build public discovery and event detail from the approved richer marketplace reference. Build focused participant home, tracker, calendar, team management, notifications and settings; organizer events, registrations, review and results; and an administrator verification queue. Bind real API operations, including consent and download grants. Display explicit timezone and absolute dates, ranking freshness and evidence. No decorative mock buttons or invented live listings.
- [ ] Implement loading, error, empty, disabled and success states; visible focus; screen-reader announcements; reduced motion; route-level access feedback; and private cache behavior. Persist sessions exclusively through the backend cookie model.
- [ ] Run `npm run typecheck`, `npm run lint`, `npm run build` and `npm run test:e2e`; inspect discovery, event detail and registration at 360, 768 and 1440 pixels and 200% zoom. Check keyboard focus and dialog return focus.
- [ ] Commit `feat: connect the Alignn marketplace and workspaces to the API`.

## Milestone 4 Reliable delivery and verified handoff

### Task 8 Reminders imports and operator recovery

**Files:** Create `domains/notifications/` modules; reminder and import job handlers; provider adapter contracts; `tests/integration/test_reminders.py`, `test_imports.py`; web operator failed-job view and `docs/runbooks/job-recovery.md`.

**Interfaces:** Produce `schedule_reminders(db, opportunity_id: UUID, deadline_version: int, now: datetime) -> int`, `sync_provider(db, provider: OpportunityProvider) -> ImportSummary`. Notification keys include recipient, event, deadline version, threshold and channel.

- [ ] Write tests proving independent seven-day, three-day and 24-hour deliveries; one in-app notification after a crash/replay; revised deadlines invalidate old jobs; closed or expired events never trigger stale reminders; and repeated provider IDs cannot duplicate an opportunity. Test per-item import failure isolation and unconfigured-provider rejection. Run the new files and verify initial failures.

```python
# In test_reminder_thresholds, advance the injected clock through all three times.
assert delivered_thresholds == {'7d', '3d', '24h'}
assert len(in_app_deliveries) == 3
# Replay each job; these assertions must still hold.
assert duplicate_delivery_count == 0
```
- [ ] Implement minute-based scheduling, deadline-version deduplication and bounded retries through Task 2. Import into moderation with a transaction/savepoint per source item. Expose administrator-only failed-job listing and audited replay, with a documented possible duplicate email after an uncertain provider timeout.
- [ ] Run those suites and rehearse a worker kill/restart without losing a registration or duplicating in-app delivery.
- [ ] Commit `feat: complete reminders and auditable job recovery`.

### Task 9 Deterministic career insights and privacy controls

**Files:** Create `domains/insights/` modules, AI adapter, privacy export/deletion handlers; `tests/unit/test_focus.py`, `tests/integration/test_insights_privacy.py`, `test_account_deletion.py`; web career-focus and privacy pages.

**Interfaces:** Produce `build_focus(db, actor: Actor, now: datetime) -> FocusOut`, `skill_gaps(db, actor, opportunity_ids: list[UUID]) -> GapOut`, `request_account_deletion(db, actor) -> DeletionReceipt`. Gap requests accept up to 20 published saved or explicitly selected opportunities.

- [ ] Write tests asserting source-linked deterministic focus with AI disabled; identical structured facts on AI timeout; no cross-user records or private resume text in provider context; and gap requests over 20 are rejected. Test immediate session revocation on deletion, export field isolation, private-object purge jobs and pseudonymous event integrity after deletion. Run the new tests and verify failures.

```python
# In test_ai_failure_preserves_facts, compare the same account and injected time.
assert timeout_result.structured == disabled_result.structured
assert all(item.source_id for item in disabled_result.items)
assert gap_request_with_21_ids.status_code == 422
assert deleted_user_session_response.status_code == 401
```
- [ ] Implement deadline/next-action/profile-gap focus and canonical skill gaps. Optional AI can paraphrase only these facts. Add export, deletion and retained-event notices. Keep advanced radar, open-ended chat, external research and course recommendations out of scope.
- [ ] Run insight/privacy tests and browser flow with the AI adapter disabled, then a simulated provider failure.
- [ ] Commit `feat: add deterministic career focus and account privacy`.

### Task 10 Production checks documentation and whole-branch review

**Files:** Update CI; add `infra/` release configuration; `docs/runbooks/{deploy,restore,security,operations}.md`; `tests/load/registration.py`; `docs/validation.md`; final README and design system documentation.

**Interfaces:** Publish reproducible commands for migrate, start web/API/worker, generate contracts, test, load-test and restore. Health endpoint checks process liveness; readiness checks database connectivity and migration compatibility without exposing internal errors.

- [ ] Run migration tests on an empty PostgreSQL instance and upgrade a previous milestone snapshot. Verify generated OpenAPI and client have no drift. Validate production startup rejects missing credentials, debug settings, unsafe origins and demo seeding.
- [ ] Run authorization, race, retry, privacy and end-to-end suites; verify 100 simultaneous last-seat attempts never overbook. Load-test 20,000 opportunities and 50 searches/second, reporting p95 and failure rates against the proposed 500 ms target. Do not claim 99.5% availability from a short test.

```text
uv run --project apps/api pytest apps/api/tests -q
npm run lint
npm run typecheck
npm run build
npm run test:e2e
```

Each command must exit zero; retain measured load-test results separately. A zero test count, missing PostgreSQL, missing browser binary or skipped critical suite is not a pass.
- [ ] Use the accessibility skill for keyboard, focus, names, forms, announcements, contrast, 200% zoom and responsive QA. Fix actionable failures; inspect generated titles, emails and source for the old product name. Record approved logo variants, semantic tokens and component patterns.
- [ ] Rehearse restore with local/staging resources where available. Document unverified provider-dependent RPO/RTO and public-launch prerequisites rather than provisioning paid services or claiming a successful production restore.
- [ ] Obtain the execution method's required whole-branch review, resolve material findings, rerun affected checks and commit `chore: verify Alignn delivery and document operations`.
- [ ] Push the completed work to the authorized private repository. Hand off the running local app, commit, test evidence and remaining operational prerequisites. Do not publish a deployment without a separate user request.

## Plan self review

All twelve specification sections map to the tasks above. Identity and permission rules map to Tasks 1 and 3; database and transactions to Tasks 1–6; API/search to Tasks 4 and 7; jobs/files/privacy to Tasks 2, 3, 8 and 9; brand and states to Task 7; operations and naming to Task 10. Every Review Focus item has owning tests. Interfaces use the same UUID, Actor, Clock and DomainError conventions throughout.

The current host has Node.js 24.14.1 and a default Python 3.9.6, below this plan's Python floor. Docker and uv were not found on PATH during the initial check. Resolve runtime availability during execution without silently changing machine-wide settings; report any required installation or use an already available supported runtime. Application tests have not run because application code does not exist yet.

The plan recommends native execution in this chat with a fresh whole-branch reviewer: the tasks share one permission model, API contract and schema, and continuity should reduce integration churn. Subagent-driven execution remains available if the user prefers independent task-by-task implementation and review. Neither approach is selected by this recommendation.
