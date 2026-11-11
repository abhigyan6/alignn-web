import "server-only";
import { apiOrigin } from "./api-origin";
import { auth } from "@clerk/nextjs/server";
import type { components } from "../../../../packages/api-client/src/schema";

export type AccountProfile = components["schemas"]["ProfileOut"];

export async function requireAccountProfile(): Promise<AccountProfile> {
  const { getToken } = await auth.protect();
  const token = await getToken();
  if (!token)
    throw new Error("Your account session is temporarily unavailable.");

  const backend = apiOrigin();
  if (!backend) throw new Error("Account service is unavailable.");
  const response = await fetch(new URL("/api/v1/me/profile", backend), {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
    redirect: "error",
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) throw new Error("Could not load your Alignn profile.");
  return response.json();
}
