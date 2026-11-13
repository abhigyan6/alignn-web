import { useCallback, useEffect, useState } from "react";
import { api, ApiError, type Opportunity } from "./api";
import { useSessionKey } from "./session-readiness";

/**
 * - "loading": the session is pending, or the read for this account is in flight.
 * - "ready": the saved IDs are the account's actual saved items (an empty set
 *   when signed out).
 * - "unknown": the read failed. Nothing is claimed about what is saved, so
 *   save controls stay disabled until a retry succeeds.
 */
export type SavedStatus = "loading" | "ready" | "unknown";

export type SavedSnapshot = {
  /** Session key the data was read for. Data for another key is never shown. */
  key: string;
  ids: ReadonlySet<string>;
  status: "ready" | "unknown";
};

const NONE: ReadonlySet<string> = new Set();

/** Pure view of a snapshot for the current session key. */
export function resolveSaved(
  snapshot: SavedSnapshot | null,
  key: string | null,
): { status: SavedStatus; ids: ReadonlySet<string> } {
  if (key === null || !snapshot || snapshot.key !== key)
    return { status: "loading", ids: NONE };
  return { status: snapshot.status, ids: snapshot.ids };
}

/** Pure outcome of one /me/saved read. */
export function savedSnapshotFor(
  key: string,
  result: { items: Pick<Opportunity, "id">[] } | { error: unknown },
): SavedSnapshot {
  if ("items" in result)
    return {
      key,
      ids: new Set(result.items.map((o) => o.id)),
      status: "ready",
    };
  // 401 means signed out: nothing is saved. Any other failure is unknown.
  return result.error instanceof ApiError && result.error.status === 401
    ? { key, ids: NONE, status: "ready" }
    : { key, ids: NONE, status: "unknown" };
}

/** Pure local update after a successful save or remove. */
export function withSaved(
  snapshot: SavedSnapshot | null,
  key: string | null,
  id: string,
  saved: boolean,
): SavedSnapshot | null {
  // Only a known set can be updated; an unknown or other-account one is left
  // as it is rather than turned into a claim about what is saved.
  if (!snapshot || key === null || snapshot.key !== key) return snapshot;
  if (snapshot.status !== "ready") return snapshot;
  const ids = new Set(snapshot.ids);
  if (saved) ids.add(id);
  else ids.delete(id);
  return { ...snapshot, ids };
}

/**
 * The student's actual saved opportunity IDs, shared by Home, Discover and
 * details. Never requests before the session is ready, and re-reads whenever
 * the session key changes (sign-in, sign-out, account switch), so one
 * account's saved state is never shown for another.
 */
export function useSavedIds() {
  const key = useSessionKey();
  const [snapshot, setSnapshot] = useState<SavedSnapshot | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (key === null) return;
    const controller = new AbortController();
    api<{ items: Opportunity[] }>("/me/saved", { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted)
          setSnapshot(savedSnapshotFor(key, data));
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setSnapshot(savedSnapshotFor(key, { error }));
      });
    return () => controller.abort();
  }, [key, attempt]);

  const { status, ids } = resolveSaved(snapshot, key);
  const setSaved = useCallback(
    (id: string, saved: boolean) =>
      setSnapshot((current) => withSaved(current, key, id, saved)),
    [key],
  );
  const retry = useCallback(() => {
    setSnapshot(null);
    setAttempt((value) => value + 1);
  }, []);

  return { status, ids, setSaved, retry };
}
