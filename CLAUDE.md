# Alignn contributor guidance

Read AGENTS.md first. The active checkout is /Users/abhigyandwivedi/Developer/alignn-web; never edit the retained iCloud backup.

## Git workflow

- Create a new `codex/<task>` branch for every task. Never push directly to main.
- Keep commits small and focused. Open a pull request describing what changed, why, how to test it, and risks/rollback. A stacked PR must name its dependency and target the parent branch until that parent is merged.
- Use Conventional Commits: `type(scope): imperative description`, e.g. `fix(auth): preserve input focus rings` or `ci: test against PostgreSQL`. Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert. Scope is optional; add `!` and a BREAKING CHANGE footer when appropriate. Never put credentials or private payloads in messages.
- Never rewrite shared history or force-push without explicit approval.

## Local commit checks

Install Node24, uv and Gitleaks (`brew install gitleaks` on macOS), then run `npm ci` and `uv sync --project apps/api --locked`. `npm run prepare` installs the repository-local `.githooks` path; it does not overwrite a different existing hooksPath. CI skips local hook installation.

The pre-commit hook scans the staged diff with Gitleaks and full redaction, runs lint-staged (ESLint/Prettier for JS/TS, Prettier for documents/styles/configuration, Ruff lint/format for Python), then scans the final staged diff again. lint-staged preserves unstaged hunks and stages its own fixes. Review formatter changes before committing. A missing scanner or dependency fails the hook; do not bypass it for convenience.

`.gitignore` protects local environment, credential, build/cache, OS and editor files. It does not untrack files already committed. Keep examples credential-free. Never print live secrets or inspect ignored authentication/env files. Run historical scans with `gitleaks git --redact=100 --log-opts="--all --reflog --full-history" .`; keep raw scan reports out of Git and share only redacted location/rule metadata. A clean scan is not proof that every possible secret is absent.

Hooks are local safeguards and can be bypassed, so required CI checks and repository protections are separate controls. Do not add a blanket scanner allowlist or disable lint rules to make checks pass.
