"use client";
import { ClerkProvider, useAuth, UserButton } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import Link from "next/link";
import { setTokenGetter } from "@/lib/api";

function SessionBridge({ children }: { children: React.ReactNode }) {
  const { isLoaded, getToken } = useAuth();
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (isLoaded) {
      setTokenGetter(() => getToken());
      setReady(true);
    }
    return () => setTokenGetter(null);
  }, [isLoaded, getToken]);
  return ready ? (
    children
  ) : (
    <main id="main" className="auth">
      <p role="status">Loading Alignn…</p>
    </main>
  );
}
export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider
      telemetry={{ disabled: true }}
      signInUrl="/login"
      signUpUrl="/signup"
      signInForceRedirectUrl="/onboarding"
      signUpForceRedirectUrl="/onboarding"
      appearance={{
        variables: {
          colorPrimary: "#2344dc",
          fontFamily: "Manrope, Arial, sans-serif",
          borderRadius: "6px",
        },
      }}
    >
      <SessionBridge>{children}</SessionBridge>
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
