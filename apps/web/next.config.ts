import type { NextConfig } from "next";
import { apiOrigin } from "./src/lib/api-origin";
const backend = apiOrigin();
const config: NextConfig = {
  agentRules: false,
  // Clerk CLI detects the monorepo root and may emit the framework-neutral public key name.
  env: {
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ||
      process.env.CLERK_PUBLISHABLE_KEY,
  },
  async rewrites() {
    if (!backend) return [];
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
    ];
  },
};
export default config;
