"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

/** Routes that render their own nav and footer (see components/marketing). */
const marketingRoutes = new Set(["/", "/privacy", "/terms", "/team"]);

export function SiteChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  if (marketingRoutes.has(pathname)) return <>{children}</>;
  return (
    <>
      <header className="site-header">
        <Link className="brand" href="/">
          <svg aria-hidden="true" viewBox="0 0 48 48">
            <path
              d="M12 12C19-2 38 9 32 22L13 37C0 42 1 20 17 20H31C49 20 47 47 30 42M31 10V34"
              fill="none"
              stroke="currentColor"
              strokeWidth="5"
              strokeLinecap="round"
            />
          </svg>
          alignn
        </Link>
      </header>
      {children}
      <footer className="site-footer">
        <strong>Find your people. Find your next step.</strong>
        <span>Alignn · Coming soon.</span>
      </footer>
    </>
  );
}
