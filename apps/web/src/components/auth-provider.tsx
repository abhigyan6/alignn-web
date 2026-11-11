"use client";
import { ClerkProvider, useAuth, UserButton } from "@clerk/nextjs";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
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
  return pathname === "/" || authPage || ready ? children : <AccountLoading />;
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
          colorPrimary: "#123e2f",
          fontFamily: "Manrope, Arial, sans-serif",
          borderRadius: "6px",
        },
      }}
    >
      {children}
    </ClerkProvider>
  );
}
export function AccountControl() {
  const { isLoaded, isSignedIn } = useAuth();
  if (!isLoaded) return <span role="status">Loading account…</span>;
  return isSignedIn ? (
    <UserButton />
  ) : (
    <Link className="button secondary" href="/login">
      Sign in
    </Link>
  );
}
