"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, User, Opportunity } from "@/lib/api";
export default function Workspace() {
  const [user, setUser] = useState<User | null>(null),
    [items, setItems] = useState<Opportunity[]>([]),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    Promise.all([api<User>("/me"), api<{ items: Opportunity[] }>("/me/saved")])
      .then(([u, s]) => {
        setUser(u);
        setItems(s.items);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);
  return (
    <main id="main" className="workspace">
      <h1>Your workspace</h1>
      {loading ? (
        <p role="status">Loading your workspace…</p>
      ) : error ? (
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
              Verify your email before joining hosted events or requesting an
              organization.
            </p>
          )}
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
          <button
            onClick={async () => {
              try {
                await api("/auth/logout", { method: "POST" });
                location.assign("/explore");
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
