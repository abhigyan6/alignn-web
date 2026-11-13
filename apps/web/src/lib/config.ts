/**
 * Web runtime configuration.
 *
 * This module is the only place where application code reads Clerk and
 * public-origin environment variables. Other modules import the named flags
 * below instead of touching `process.env` directly.
 *
 * Rules:
 * - Keep `process.env.NAME` written literally. Next.js inlines NEXT_PUBLIC_*
 *   values at build time only for literal references.
 * - Never export a secret value. Export only booleans derived from secrets.
 * - The API origin is validated in `api-origin.ts`, which is read by
 *   `next.config.ts` at build time.
 */

/** True when the browser-safe Clerk publishable key is present. */
export const isClerkPublishableKeyConfigured = Boolean(
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
);

/**
 * True when both the publishable key and the server-side secret are present.
 * Server components and middleware need both before they can call Clerk.
 */
export const isClerkServerConfigured = Boolean(
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && process.env.CLERK_SECRET_KEY,
);

/** Origin Clerk should accept tokens for. Local development fallback applies. */
export const publicOrigin =
  process.env.PUBLIC_ORIGIN ?? "http://localhost:3000";
