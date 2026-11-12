"use client";
import { ClerkProvider, useAuth, UserButton } from "@clerk/nextjs";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import DiscoveryLoading from "@/components/discovery-loading";
import AccountLoading from "@/components/account-loading";
import { setTokenGetter } from "@/lib/api";

export function SessionBridge({ children }: { children: React.ReactNode }) {
  const { isLoaded, getToken } = useAuth();
  const pathname = usePathname();
  const getTokenRef = useRef(getToken);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    getTokenRef.current = getToken;
  }, [getToken]);

  useEffect(() => {
    if (!isLoaded) return;
    setTokenGetter(() => getTokenRef.current());
    setReady(true);
    return () => setTokenGetter(null);
  }, [isLoaded]);

  const authPage =
    pathname === "/login" ||
    pathname.startsWith("/login/") ||
    pathname === "/signup" ||
    pathname.startsWith("/signup/");
  if (!ready && pathname === "/explore") return <DiscoveryLoading />;
  const publicPolicy = ["/privacy", "/terms", "/cookies"].includes(pathname);
  return pathname === "/" || publicPolicy || authPage || ready ? (
    children
  ) : (
    <AccountLoading onboarding={pathname.startsWith("/onboarding")} />
  );
}
export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider
      telemetry={{ disabled: true }}
      signInUrl="/login"
      signUpUrl="/signup"
      signInFallbackRedirectUrl="/auth/redirect"
      signUpFallbackRedirectUrl="/auth/redirect"
      appearance={{
        variables: {
          colorPrimary: "#145640",
          fontFamily: "Manrope, Arial, sans-serif",
          borderRadius: "10px",
        },
      }}
    >
      {children}
    </ClerkProvider>
  );
}
export function AccountControl() {
  const { isLoaded, isSignedIn } = useAuth();
  if (!isLoaded)
    return (
      <span className="account-placeholder" role="status">
        <span className="sr-only">Loading account…</span>
      </span>
    );
  return isSignedIn ? (
    <UserButton />
  ) : (
    <Link className="button secondary" href="/login">
      Sign in
    </Link>
  );
}
