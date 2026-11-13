# Configuration refactor baseline

13 November 2026. Approved design: codebase organization; approved first-packet plan: configuration boundaries. Codex coordinates, reviews, verifies and handles Git; Claude Code implements bounded source changes. This is a source checkpoint, not production acceptance.

## Branch ownership

- Implementation branch: `codex/web-config-boundaries`, from fetched `codex/version-control-hygiene` at `0b95ee461d1293c73bab95803d5c113739236326`.
- [PR #3](https://github.com/abhigyan6/alignn-web/pull/3) remains open against `codex/audit-vercel-recovery`; it is this packet's parent dependency.
- [Configuration PR #6](https://github.com/abhigyan6/alignn-web/pull/6) merged into that hygiene baseline. Extend its config module; do not duplicate the earlier centralization.
- [Session-readiness PR #7](https://github.com/abhigyan6/alignn-web/pull/7) remains open at `5440d34`. Its code is absent from this baseline and is not copied into this packet. Reconcile its configuration import through a later reviewed integration.
- [Design PR #8](https://github.com/abhigyan6/alignn-web/pull/8) and [plan PR #9](https://github.com/abhigyan6/alignn-web/pull/9) carry the approved documents on separate documentation lineages. The coding PR targets the hygiene branch, not those documentation branches.

No merge, retarget, closure, branch deletion or history rewrite is part of this packet. The entire organization refactor continues feature by feature after this first packet.

## Preserved work and limits

The pre-existing modified `README.md`, untracked `HANDOFF.md`, `handover.md`, `docs/handover/` and `docs/tri-agent/` remain outside task commits. Existing configuration, auth caches, uploads, runtime data and the iCloud backup are not inspected or changed.

The packet separates public and server-only configuration while preserving presence checks, public-origin fallback, route guards and API-origin validation. FastAPI owns authorization/business writes. No API/database, infrastructure, provider or deployment change is included.

Historical test reports on earlier PRs do not validate the new extraction. Record fresh focused synthetic tests, lint, typecheck, build and review evidence in the implementation PR. Real Clerk login, account switching, production settings and deployed behavior remain unverified by this packet.
