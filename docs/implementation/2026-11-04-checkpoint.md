# Revised design implementation checkpoint

This is a partial implementation of the 4 November design revision. The previous implementation plan remains historical; do not mark its full frontend or operations tasks complete from this checkpoint.

Implemented now:

- RegistrationOut requires nullable team_id and an eligibility_snapshot_id UUID, plus roster_user_ids and a current request_id. OpenAPI and TypeScript contracts are regenerated.
- A forward migration creates standalone admission snapshots and backfills historical policy/evidence and stored registration replay responses. Successful registration transitions from transaction-local PENDING to CONFIRMED.
- Organizer participant-list and consent-based file reads require current organization verification. An administrator who belongs to an organization cannot verify it.
- A real Next.js interface serves discovery/category/search, opportunity detail, save and external-tracker creation, login/signup, verification/reset links and a saved-opportunities workspace. Backend cookies and CSRF remain authoritative. No synthetic listings are presented as live data.
- Manrope is served from the bundled npm font package under its SIL OFL license. The loop is an original proposed SVG variation.

Verified locally: 53 PostgreSQL API tests; 6 Chrome desktop/mobile browser tests; frontend strict type check, formatting check and optimized production build; Ruff; Alembic no-drift check. Browser tests cover real discovery requests, invalid sign-in and missing verification tokens. These results do not verify complete signup/email delivery, event participation or production readiness. No load, availability or legal compliance claim is made.

Still required: revised endpoint rate/cooldown budgets and in-flight request timeout handling; complete organizer evidence/revocation workflow; frozen-member withdrawal policy; account deletion/retention/export cleanup; full profile and external-tracker UI; organizer/admin UI; submission/judging/results; reminders/imports/career focus; deployment and restore validation. Current code still uses the earlier worker FAILED state rather than the revised DEAD_LETTER contract. Implement these explicitly before claiming the revised design is complete.

Run the web app with `NEXT_TELEMETRY_DISABLED=1 npm run dev` alongside FastAPI on 8000. Open http://localhost:3000/explore. The old 58214 HTML is only a design reference. See the local-development runbook for PostgreSQL, worker and SMTP requirements.
