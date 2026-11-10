"use client";
import { ClerkProvider, useAuth, UserButton } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import Link from "next/link";
import AccountLoading from "@/components/account-loading";
import { setTokenGetter } from "@/lib/api";

export function SessionBridge({ children }: { children: React.ReactNode }) {
  const { isLoaded, getToken } = useAuth();
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (isLoaded) {
      setTokenGetter(() => getToken());
      setReady(true);
    }
    return () => setTokenGetter(null);
  }, [isLoaded, getToken]);
  return ready ? children : <AccountLoading />;
}
export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider
      telemetry={{ disabled: true }}
      signInUrl="/login"
      signUpUrl="/signup"
      signInForceRedirectUrl="/workspace"
      signUpForceRedirectUrl="/onboarding"
      appearance={{
        variables: {
          colorPrimary: "#2344dc",
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
