import "server-only";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import type { components } from "../../../../packages/api-client/src/schema";

export type AccountProfile = components["schemas"]["ProfileOut"];

export async function requireAccountProfile(): Promise<AccountProfile> {
  const { getToken } = await auth.protect();
  const token = await getToken();
  if (!token) redirect("/login");

  const apiOrigin = process.env.API_ORIGIN || "http://127.0.0.1:8000";
  const response = await fetch(new URL("/api/v1/me/profile", apiOrigin), {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
    redirect: "error",
  });
  if (!response.ok) throw new Error("Could not load your Alignn profile.");
  return response.json();
}
