import "server-only";

import { isClerkPublishableKeyConfigured } from "./client";

/**
 * Server-only web configuration.
 *
 * Never export a secret value. Export only booleans derived from secrets.
 * The API origin is validated in `api-origin.ts`, which `next.config.ts`
 * reads at build time.
 */

/**
 * True when both the publishable key and the server-side secret are present.
 * Server components and middleware need both before they can call Clerk.
 */
export const isClerkServerConfigured = Boolean(
  isClerkPublishableKeyConfigured && process.env.CLERK_SECRET_KEY,
);

/** Origin Clerk should accept tokens for. Local development fallback applies. */
export const publicOrigin =
  process.env.PUBLIC_ORIGIN ?? "http://localhost:3000";
