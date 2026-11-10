import type { NextConfig } from "next";
const apiOrigin = new URL(process.env.API_ORIGIN || "http://127.0.0.1:8000");
if (
  !["http:", "https:"].includes(apiOrigin.protocol) ||
  apiOrigin.username ||
  apiOrigin.password ||
  apiOrigin.pathname !== "/" ||
  apiOrigin.search ||
  apiOrigin.hash
) {
  throw new Error(
    "API_ORIGIN must be an HTTP(S) origin without credentials or a path",
  );
}
const config: NextConfig = {
  agentRules: false,
  // Clerk CLI detects the monorepo root and may emit the framework-neutral public key name.
  env: {
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ||
      process.env.CLERK_PUBLISHABLE_KEY,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin.origin}/api/:path*`,
      },
    ];
  },
};
export default config;
