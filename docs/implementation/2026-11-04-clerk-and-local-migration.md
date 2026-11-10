# Clerk and local-storage checkpoint — 4 November 2026

Active repository: `/Users/abhigyandwivedi/Developer/alignn-web`, branch `codex/build-alignn`. Former checkout at `/Users/abhigyandwivedi/Documents/Codex/2026-11-03/co/alignn-web` remains intact as an iCloud backup; later edits belong only in the active checkout. No commit, push or public deployment was made for this checkpoint.

## Authentication changes

Official Next.js and Python Clerk SDKs installed and locked. Existing selected application linked; development keys saved privately. Clerk provider, sign-in/sign-up, account menu, session-token API calls, route-level protection and Clerk logout replace browser use of opaque local sessions. The local UUID is mapped through unique `users.clerk_subject`; legacy password hashes become nullable. The migration preserves existing users and profiles, rejects email collisions and does not trust metadata or browser-provided administrator roles. SDK verification is limited to session tokens, the configured Origin/authorized party and valid time/signature claims. Pending sessions, inactive users and legacy cookies fail closed. Verified email and remote account availability are checked on each authenticated request.

New users reach education, canonical skills/interests and optional private resume upload before their workspace. Returning users with degree and graduation year go to the workspace; edit mode reopens setup. Resume scanning is connected through existing jobs; parsing is explicitly pending. Workspace is still primarily saved opportunities, not the finished personalized dashboard. Source collectors are still pending. No real Clerk users were created by the agent, and completed Google/email sign-in was not tested on a real account.

## Local migration and recovery

Finder showed full iCloud storage; offloaded runtime, source, Git and build files timed out. Source and full Git history were recovered with coordinated macOS reads and copied outside Documents. `git fsck --full --no-reflogs` passes, preserving HEAD `77ef8b92c08bbecaf0a4a0062f0667fdfc15996e` and uncommitted work. Node dependencies/build outputs were rebuilt. A fresh durable Python runtime and virtual environment are in the new checkout. Credentials remain ignored and private.

The PostgreSQL 18 cluster was cleanly stopped and copied; provably zero-byte files and PostgreSQL 18 version markers were recreated. Its standard 88-byte `postgresql.auto.conf` comment was restored, and startup regenerated `postmaster.opts`. No nonempty relation data was synthesized. PostgreSQL now reports the new storage directory and schema `71d2a4b6c801`. Local scanner and Mailpit paths were updated and restarted.

Remaining limitation: 32 old upload objects still could not be materialized by iCloud after coordinated recovery attempts. Their originals have not been deleted. The private manifest is `.superpowers/migration-pending-uploads.json`. One is referenced by the development database: `alignn-local-check.pdf`, 68 bytes, a prior local scan-test fixture. That download remains unavailable in the new checkout. Other pending objects are not referenced by the current development file table. Do not delete the old checkout until recovery is resolved or the owner explicitly approves disposition of these test artifacts. No replacement PDF contents were invented.

## Verification from the active checkout

- 66 PostgreSQL-backed API tests passed, including actual RSA token-verification cases, Origin checks, no email auto-linking, local-cookie rejection and local-role enforcement.
- 8 desktop/mobile browser tests passed: live discovery/filtering, Clerk sign-in controls, signed-out workspace redirect and legacy recovery redirect.
- Production build, TypeScript compilation, Prettier, Ruff and Alembic drift checks passed.
- API readiness and PostgreSQL storage-path checks passed. No production SLO or compliance claim is made.

Next required work: a real user's sign-in/onboarding confirmation, source collection and resume parsing, full personalized workspace, privacy/deprovisioning and other existing launch requirements. A reviewed existing-account migration is required before importing any old users. The incubator-demo scope in older documents does not replace the user's request for a real full product.
