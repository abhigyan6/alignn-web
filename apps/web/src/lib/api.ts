import type { components } from "../../../../packages/api-client/src/schema";
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
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = init.method ?? "GET";
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD"].includes(method)) {
    let csrf = document.cookie
      .split("; ")
      .find((x) => x.startsWith("alignn_csrf="))
      ?.split("=")[1];
    if (!csrf) {
      await fetch("/api/v1/auth/csrf", {
        credentials: "same-origin",
        cache: "no-store",
      });
      csrf = document.cookie
        .split("; ")
        .find((x) => x.startsWith("alignn_csrf="))
        ?.split("=")[1];
    }
    if (csrf) headers.set("X-CSRF-Token", decodeURIComponent(csrf));
  }
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
