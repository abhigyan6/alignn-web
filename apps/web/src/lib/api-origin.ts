export function apiOrigin(): string | null {
  const configured = process.env.API_ORIGIN;
  if (!configured && process.env.VERCEL) return null;
  const origin = new URL(configured || "http://127.0.0.1:8000");
  if (
    !["http:", "https:"].includes(origin.protocol) ||
    origin.username ||
    origin.password ||
    origin.pathname !== "/" ||
    origin.search ||
    origin.hash ||
    (process.env.VERCEL &&
      (origin.protocol !== "https:" ||
        ["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname)))
  )
    throw new Error(
      "API_ORIGIN must be a backend origin without credentials or a path; Vercel requires public HTTPS.",
    );
  return origin.origin;
}
