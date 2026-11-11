"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AccountControl } from "@/components/auth-provider";

export default function AppNavigation({
  authenticated,
}: {
  authenticated: boolean;
}) {
  const pathname = usePathname();
  if (
    pathname === "/" ||
    pathname.startsWith("/login") ||
    pathname.startsWith("/signup")
  )
    return null;
  const discovering =
    pathname === "/explore" || pathname.startsWith("/opportunities/");
  return (
    <>
      <nav className="app-navigation" aria-label="Main navigation">
        <Link href="/explore" aria-current={discovering ? "page" : undefined}>
          Discover
        </Link>
        <Link
          href="/workspace"
          prefetch={false}
          aria-current={pathname === "/workspace" ? "page" : undefined}
        >
          My workspace
        </Link>
      </nav>
      <div className="header-account">
        {authenticated ? (
          <AccountControl />
        ) : (
          <Link className="button secondary" href="/login">
            Sign in
          </Link>
        )}
      </div>
    </>
  );
}
