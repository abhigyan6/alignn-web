/**
 * Public (browser-safe) web configuration.
 *
 * Keep `process.env.NEXT_PUBLIC_*` written literally: Next.js inlines these
 * values at build time only for literal references. Never read or export
 * private configuration from this module.
 */

/** True when the browser-safe Clerk publishable key is present. */
export const isClerkPublishableKeyConfigured = Boolean(
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
);
