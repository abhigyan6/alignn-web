import { useSyncExternalStore } from "react";

/**
 * Client session-readiness contract.
 *
 * The session key answers two questions at once:
 * - null: the Clerk token bridge is not installed yet, so requests cannot
 *   carry the student's verified session token ("pending").
 * - a string: the bridge is installed (or Clerk is not configured, so there is
 *   no bridge to wait for). The string names who the session belongs to, so a
 *   sign-in, sign-out or account switch yields a different key while readiness
 *   stays "ready". Anything cached per account must be keyed by it.
 *
 * This only controls request timing and cache scoping. Authorization remains
 * server-owned.
 */
export type SessionKey = string | null;

/** Key used when the session is ready but nobody is signed in. */
export const ANONYMOUS_SESSION = "anonymous";

export function sessionKeyFor(userId: string | null | undefined): string {
  return userId ? `user:${userId}` : ANONYMOUS_SESSION;
}

// The same build-time value decides whether layout.tsx mounts SessionBridge.
const clerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
const initialKey: SessionKey = clerkConfigured ? null : ANONYMOUS_SESSION;
let sessionKey: SessionKey = initialKey;
const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function setSessionKey(next: SessionKey) {
  if (sessionKey === next) return;
  sessionKey = next;
  for (const listener of [...listeners]) listener();
}

/** The token bridge is gone or not installed yet. */
export function markSessionPending() {
  setSessionKey(null);
}

/** The token bridge is installed for this user (null user means signed out). */
export function markSessionReady(userId: string | null | undefined) {
  setSessionKey(sessionKeyFor(userId));
}

export function isSessionReady() {
  return sessionKey !== null;
}

/** Non-hook read of the current key, for request code and tests. */
export function getSessionKey(): SessionKey {
  return sessionKey;
}

export function useSessionReady() {
  return useSyncExternalStore(
    subscribe,
    () => sessionKey !== null,
    () => initialKey !== null,
  );
}

/** Null while pending; otherwise the key to scope per-account state by. */
export function useSessionKey(): SessionKey {
  return useSyncExternalStore(
    subscribe,
    () => sessionKey,
    () => initialKey,
  );
}

export const SESSION_WAIT_MS = 10_000;

/**
 * Resolves true once the session is ready, false if it is still pending after
 * SESSION_WAIT_MS, and rejects if the signal aborts first.
 */
export function waitForSession(signal?: AbortSignal | null): Promise<boolean> {
  if (sessionKey !== null) return Promise.resolve(true);
  return new Promise<boolean>((resolve, reject) => {
    let unsubscribe = () => {};
    const finish = (settle: () => void) => {
      clearTimeout(timer);
      unsubscribe();
      signal?.removeEventListener("abort", onAbort);
      settle();
    };
    const onAbort = () =>
      finish(() =>
        reject(signal?.reason ?? new DOMException("Aborted", "AbortError")),
      );
    const timer = setTimeout(
      () => finish(() => resolve(false)),
      SESSION_WAIT_MS,
    );
    if (signal?.aborted) return onAbort();
    unsubscribe = subscribe(() => {
      if (sessionKey !== null) finish(() => resolve(true));
    });
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}
