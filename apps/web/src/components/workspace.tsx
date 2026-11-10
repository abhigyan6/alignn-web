"use client";
import Link from "next/link";
import { useClerk } from "@clerk/nextjs";
import AccountLoading from "@/components/account-loading";
import { useEffect, useState } from "react";
import { api, User, Opportunity } from "@/lib/api";
import ApplicationTracker from "@/components/application-tracker";
export default function Workspace() {
  const { signOut } = useClerk();
  const [user, setUser] = useState<User | null>(null),
    [items, setItems] = useState<Opportunity[]>([]),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };
    Promise.all([
      api<User>("/me", options),
      api<{ items: Opportunity[] }>("/me/saved", options),
    ])
      .then(([u, s]) => {
        if (controller.signal.aborted) return;
        setUser(u);
        setItems(s.items);
        setLoading(false);
      })
      .catch((e) => {
        if (controller.signal.aborted) return;
        setError(e.message);
        setLoading(false);
      });
    return () => controller.abort();
  }, []);
  if (loading) return <AccountLoading />;
  return (
    <main id="main" className="workspace">
      <h1>Your workspace</h1>
      {error ? (
        <div className="empty">
          <h2>Sign in to continue.</h2>
          <p role="alert">{error}</p>
          <Link className="button" href="/login">
            Sign in
          </Link>
        </div>
      ) : (
        <>
          <p>{user?.full_name}, keep the opportunities that matter close.</p>
          {!user?.is_verified && (
            <p role="status">
              Verify your email before requesting an organization.
            </p>
          )}
          <Link href="/onboarding?edit=1">Edit your profile ↗</Link>
          <section>
            <h2>Saved opportunities</h2>
            {items.length ? (
              items.map((o) => (
                <Link
                  className="saved-row"
                  key={o.id}
                  href={"/opportunities/" + o.id}
                >
                  <strong>{o.title}</strong>
                  <span>{o.organization_name} ↗</span>
                </Link>
              ))
            ) : (
              <div className="empty">
                <h3>A shortlist starts with one possibility.</h3>
                <p>Save opportunities from discovery to see them here.</p>
                <Link href="/explore">Explore opportunities ↗</Link>
              </div>
            )}
          </section>
          <ApplicationTracker />
          <button
            onClick={async () => {
              try {
                await signOut({ redirectUrl: "/explore" });
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            Sign out
          </button>
        </>
      )}
    </main>
  );
}
