# Web configuration boundaries

13 November 2026. Describes how `apps/web` reads configuration after the split of the former single config module. Source checkpoint, not production acceptance. Variable names only; no values or environment files are recorded here.

## Variables and ownership

| Variable                            | Kind                         | Read in                    | Exposed as                               |
| ----------------------------------- | ---------------------------- | -------------------------- | ---------------------------------------- |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Public, inlined at build     | `src/lib/config/client.ts` | `isClerkPublishableKeyConfigured`        |
| `CLERK_SECRET_KEY`                  | Private, server only         | `src/lib/config/server.ts` | Only via `isClerkServerConfigured`       |
| `PUBLIC_ORIGIN`                     | Server module initialization | `src/lib/config/server.ts` | `publicOrigin`                           |
| `API_ORIGIN`                        | Build time, validated        | `src/lib/api-origin.ts`    | Consumed by `next.config.ts` (unchanged) |

Secret values are never exported; only booleans derived from them.

## Explicit module imports

- `@/lib/config/client`: browser-safe. Used by `app/layout.tsx`. Must not read, import or re-export private names.
- `@/lib/config/server`: begins with `import "server-only"`, so bundling it into client code fails the build. It imports `isClerkPublishableKeyConfigured` from `./client` rather than re-reading the public variable. Used by `proxy.ts`, login, signup, onboarding and workspace.
- No compatibility barrel remains.

## Build-time limitations

- `NEXT_PUBLIC_*` values are inlined only for literal `process.env.NAME` references. Do not use dynamic lookups or destructuring.
- The public key is fixed at build; changing it requires a rebuild.
- Presence checks only: keys are not parsed or validated here.

## Known limitations (unchanged by this packet)

- **Origin fallback risk:** when `PUBLIC_ORIGIN` is missing, `publicOrigin` falls back to the local development origin; when empty, it stays empty. This preserves existing behavior and is not an approval of the policy. Origin validation for the API lives in `api-origin.ts`.
- **Backend env-file coupling:** the API and web environments are still coupled through shared environment files. Migration is deferred.
- **PR #7 readiness:** session-readiness PR #7 is not in this baseline. Reconciling its configuration import is pending a later reviewed integration.

## Commands and evidence boundaries

Focused test: `npm exec --workspace @alignn/web -- playwright test tests/config.spec.ts --project=desktop --workers=1`. Root checks: `npm run lint:js`, `npm run lint`, `npm run typecheck`, `npm run build`. The tests use synthetic values in an isolated VM and launch no browser, provider or network. Real Clerk login and deployed behavior are not verified by this packet.
