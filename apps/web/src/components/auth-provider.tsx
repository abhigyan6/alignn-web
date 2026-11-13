"use client";
import { ClerkProvider, useAuth, UserButton } from "@clerk/nextjs";
import { useLayoutEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import AccountLoading from "@/components/account-loading";
import { setTokenGetter } from "@/lib/api";
import {
  markSessionPending,
  markSessionReady,
  useSessionReady,
} from "@/lib/session-readiness";

// Routes readable before Clerk finishes loading. Their protected requests
// still wait for the token bridge inside the shared api helper.
function isPublicRoute(pathname: string) {
  return (
    pathname === "/" ||
    pathname === "/explore" ||
    pathname.startsWith("/opportunities/") ||
    ["/privacy", "/terms", "/cookies"].includes(pathname) ||
    pathname === "/login" ||
    pathname.startsWith("/login/") ||
    pathname === "/signup" ||
    pathname.startsWith("/signup/")
  );
}

export function SessionBridge({ children }: { children: React.ReactNode }) {
  const { isLoaded, userId, getToken } = useAuth();
  const pathname = usePathname();
  const getTokenRef = useRef(getToken);
  const ready = useSessionReady();

  // Layout effects run before children's passive data-loading effects, so the
  // session key is accurate before any page issues its first request. This
  // one is declared first so the getter below never reads a previous
  // account's getToken after a sign-in, sign-out or account switch.
  useLayoutEffect(() => {
    getTokenRef.current = getToken;
  });

  // Re-runs when the signed-in user changes, publishing a new session key so
  // per-account state (saved items, personalized ranking) is read again.
  useLayoutEffect(() => {
    if (!isLoaded) {
      markSessionPending();
      return;
    }
    setTokenGetter(() => getTokenRef.current());
    markSessionReady(userId);
    return () => {
      markSessionPending();
      setTokenGetter(null);
    };
  }, [isLoaded, userId]);

  return ready || isPublicRoute(pathname) ? (
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
