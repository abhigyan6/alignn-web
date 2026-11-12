"use client";
import Link from "next/link";
import { Suspense } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { AccountControl } from "@/components/auth-provider";
import Icon from "@/components/icon";

function Navigation({ authenticated }: { authenticated: boolean }) {
  const pathname = usePathname(),
    params = useSearchParams();
  const authPage =
    pathname.startsWith("/login") || pathname.startsWith("/signup");
  if (authPage)
    return (
      <Link className="auth-back-link" href="/explore">
        Browse opportunities <Icon name="arrow" size={17} />
      </Link>
    );
  const tab = params.get("tab") ?? "saved";
  const links = [
    {
      label: "Discover",
      href: "/explore",
      icon: "grid" as const,
      active: pathname === "/explore" || pathname.startsWith("/opportunities/"),
    },
    {
      label: "Saved",
      href: "/workspace?tab=saved",
      icon: "bookmark" as const,
      active: pathname === "/workspace" && tab !== "applications",
    },
    {
      label: "Applications",
      href: "/workspace?tab=applications",
      icon: "briefcase" as const,
      active: pathname === "/workspace" && tab === "applications",
    },
    {
      label: "Profile",
      href: "/onboarding?edit=1",
      icon: "user" as const,
      active: pathname === "/onboarding",
    },
  ];
  return (
    <>
      <nav className="app-navigation" aria-label="Main navigation">
        {links.map((link) => (
          <Link
            key={link.label}
            href={link.href}
            prefetch={link.href === "/explore"}
            aria-current={link.active ? "page" : undefined}
          >
            <Icon name={link.icon} size={18} />
            {link.label}
          </Link>
        ))}
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
export default function AppNavigation(props: { authenticated: boolean }) {
  return (
    <Suspense
      fallback={<div className="navigation-placeholder" aria-hidden="true" />}
    >
      <Navigation {...props} />
    </Suspense>
  );
}
