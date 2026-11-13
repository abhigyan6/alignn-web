import type { components } from "../../../../packages/api-client/src/schema";
import { waitForSession } from "./session-readiness";
export type Opportunity = components["schemas"]["OpportunityOut"];
export type User = components["schemas"]["UserOut"];
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
let tokenGetter: (() => Promise<string | null>) | null = null;
export function setTokenGetter(getter: (() => Promise<string | null>) | null) {
  tokenGetter = getter;
}
// Public catalog list/detail reads may run before the Clerk token bridge is
// ready. Every other request (account reads, fit checks and all mutations)
// waits for readiness so it is not sent without the student's session token.
// This is request timing only; the API remains the authority.
const publicCatalogRead = /^\/opportunities(?:\/[^/?#]+)?(?:[?#]|$)/;
export function isPublicCatalogRead(path: string, method = "GET") {
  return method.toUpperCase() === "GET" && publicCatalogRead.test(path);
}
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (
    !isPublicCatalogRead(path, init.method) &&
    !(await waitForSession(init.signal))
  )
    throw new ApiError(
      0,
      "Your account is still loading. Please try again in a moment.",
    );
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");
  const token = await tokenGetter?.();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch("/api/v1" + path, {
    ...init,
    headers,
    credentials: "same-origin",
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      body.error?.message ??
        "Unable to complete this request. Please try again.",
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
