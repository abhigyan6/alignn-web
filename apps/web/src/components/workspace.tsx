"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import AccountLoading from "@/components/account-loading";
import ApplicationTracker from "@/components/application-tracker";
import OpportunityCard, { isClosed } from "@/components/opportunity-card";
import { api, ApiError, type Opportunity, type User } from "@/lib/api";
import styles from "./workspace.module.css";

type SavedFilter = "all" | "active" | "closed";

function ShortlistIcon() {
  return (
    <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path d="M10 6h12a2 2 0 0 1 2 2v20l-8-5-8 5V8a2 2 0 0 1 2-2Z" />
      <path d="M12 12h8M12 16h5" />
    </svg>
  );
}

function WorkspaceScreen() {
  const params = useSearchParams();
  const tab = params.get("tab") === "applications" ? "applications" : "saved";
  const [user, setUser] = useState<User | null>(null);
  const [accountError, setAccountError] = useState("");
  const [accountAttempt, setAccountAttempt] = useState(0);
  const [items, setItems] = useState<Opportunity[] | null>(null);
  const [savedError, setSavedError] = useState("");
  const [sessionExpired, setSessionExpired] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [filter, setFilter] = useState<SavedFilter>("all");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setAccountError("");
    api<User>("/me", { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) setUser(data);
      })
      .catch((error: Error) => {
        if (!controller.signal.aborted) setAccountError(error.message);
      });
    return () => controller.abort();
  }, [accountAttempt]);

  useEffect(() => {
    if (tab !== "saved") return;
    const controller = new AbortController();
    setSavedError("");
    setSessionExpired(false);
    api<{ items: Opportunity[] }>("/me/saved", { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) setItems(data.items);
      })
      .catch((error: Error) => {
        if (controller.signal.aborted) return;
        setSavedError(error.message);
        setSessionExpired(error instanceof ApiError && error.status === 401);
      });
    return () => controller.abort();
  }, [tab, attempt]);

  const active = (items ?? []).filter((item) => !isClosed(item));
  const closed = (items ?? []).filter(isClosed);
  const shown =
    filter === "active" ? active : filter === "closed" ? closed : (items ?? []);
  const firstName = user?.full_name.trim().split(/\s+/)[0];
  const initials = user?.full_name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("");

  return (
    <main id="main" className={styles.workspace}>
      <header className={styles.pageHeading}>
        <div>
          <p className={styles.kicker}>Your next steps</p>
          <h1>
            {tab === "saved" ? "Saved opportunities" : "Your applications"}
          </h1>
          <p className={styles.lead}>
            {tab === "saved"
              ? "A shortlist worth coming back to. Keep the possibilities that interest you in one place."
              : "Keep a clear record of where you applied and what happens next."}
          </p>
        </div>
        <Link className="button secondary" href="/explore">
          Discover opportunities <span aria-hidden="true">↗</span>
        </Link>
      </header>

      <nav className={styles.tabs} aria-label="Workspace sections">
        <Link
          href="/workspace?tab=saved"
          aria-current={tab === "saved" ? "page" : undefined}
        >
          Saved opportunities
          {items && <span className={styles.tabCount}>{items.length}</span>}
        </Link>
        <Link
          href="/workspace?tab=applications"
          aria-current={tab === "applications" ? "page" : undefined}
        >
          Applications
        </Link>
      </nav>

      <div className={styles.workspaceGrid}>
        <div className={styles.mainColumn}>
          {tab === "applications" ? (
            <ApplicationTracker />
          ) : savedError ? (
            <section
              className={styles.emptyState}
              aria-labelledby="saved-error-title"
            >
              <span className={styles.emptyIcon}>
                <ShortlistIcon />
              </span>
              <h2 id="saved-error-title">Unable to load your shortlist</h2>
              <p role="alert">{savedError}</p>
              {sessionExpired ? (
                <Link className="button" href="/login">
                  Sign in again
                </Link>
              ) : (
                <button
                  className="button"
                  onClick={() => setAttempt((value) => value + 1)}
                >
                  Try again
                </button>
              )}
            </section>
          ) : items === null ? (
            <section aria-busy="true" aria-label="Loading saved opportunities">
              <span role="status" className="sr-only">
                Loading your shortlist…
              </span>
              <div className={styles.savedGrid} aria-hidden="true">
                {[0, 1, 2, 3].map((item) => (
                  <div className={styles.cardPlaceholder} key={item}>
                    <span />
                    <span />
                    <span />
                  </div>
                ))}
              </div>
            </section>
          ) : items.length === 0 ? (
            <section
              className={styles.emptyState}
              aria-labelledby="saved-empty-title"
            >
              <span className={styles.emptyIcon}>
                <ShortlistIcon />
              </span>
              <p className={styles.kicker}>Room for your next opportunity</p>
              <h2 id="saved-empty-title">Start with one worth saving.</h2>
              <p>
                Save an internship, hackathon or event while you explore. You
                can compare the details and decide when you’re ready.
              </p>
              <Link className="button" href="/explore">
                Find an opportunity <span aria-hidden="true">↗</span>
              </Link>
              <p className={styles.emptyNote}>
                Saving keeps it here. It doesn’t send an application.
              </p>
            </section>
          ) : (
            <section aria-labelledby="shortlist-title">
              <div className={styles.sectionToolbar}>
                <h2 id="shortlist-title">
                  Your shortlist <span>{shown.length}</span>
                </h2>
                <div
                  className={styles.filterGroup}
                  role="group"
                  aria-label="Filter saved opportunities"
                >
                  {(
                    [
                      ["all", "All", items.length],
                      ["active", "Active", active.length],
                      ["closed", "Closed", closed.length],
                    ] as const
                  ).map(([value, label, count]) => (
                    <button
                      key={value}
                      type="button"
                      aria-pressed={filter === value}
                      onClick={() => setFilter(value)}
                    >
                      {label} <span>{count}</span>
                    </button>
                  ))}
                </div>
              </div>
              <p role="status" className={styles.liveNotice}>
                {notice}
              </p>
              {shown.length ? (
                <div className={styles.savedGrid}>
                  {shown.map((opportunity) => (
                    <OpportunityCard
                      key={opportunity.id}
                      opportunity={opportunity}
                      saved
                      onSavedChange={(saved) => {
                        if (!saved) {
                          setItems(
                            (current) =>
                              current?.filter(
                                (item) => item.id !== opportunity.id,
                              ) ?? [],
                          );
                          setNotice("Opportunity removed from saved.");
                        }
                      }}
                    />
                  ))}
                </div>
              ) : (
                <div className={styles.filteredEmpty}>
                  <h3>
                    {filter === "closed"
                      ? "No closed opportunities here."
                      : "No active opportunities in this shortlist."}
                  </h3>
                  <p>
                    {filter === "closed"
                      ? "Closed listings you saved will stay available here for reference."
                      : "You can still read closed listings, or explore something new."}
                  </p>
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() => setFilter("all")}
                  >
                    Show all saved
                  </button>
                </div>
              )}
              {items.length >= 100 && (
                <p className={styles.collectionNote}>
                  Showing up to 100 saved opportunities.
                </p>
              )}
            </section>
          )}
        </div>

        <aside
          className={styles.accountColumn}
          aria-label="Your profile and next steps"
        >
          <section className={styles.profileCard}>
            <span className={styles.avatar} aria-hidden="true">
              {initials || "A"}
            </span>
            <p className={styles.kicker}>Your profile</p>
            <h2>
              {firstName
                ? `${firstName}, make it yours.`
                : "Make your profile work for you."}
            </h2>
            <p>
              Your education, skills and preferences help shape the
              opportunities you see.
            </p>
            <Link href="/onboarding?edit=1" className={styles.textLink}>
              Edit your profile <span aria-hidden="true">↗</span>
            </Link>
            {user && !user.is_verified && (
              <p className={styles.accountNote}>
                Verify your email to keep your account ready.
              </p>
            )}
            {accountError && (
              <div className={styles.accountNote}>
                <p role="alert">Unable to load account details.</p>
                <button
                  type="button"
                  onClick={() => setAccountAttempt((value) => value + 1)}
                >
                  Retry account details
                </button>
              </div>
            )}
          </section>
          <section className={styles.guideCard}>
            <p className={styles.kicker}>A little clarity</p>
            <h2>Saved isn’t applied.</h2>
            <p>
              Apply on the original website. Then update your application stage
              here so your next step stays clear.
            </p>
            <Link
              href={
                tab === "saved" ? "/workspace?tab=applications" : "/explore"
              }
              className={styles.textLink}
            >
              {tab === "saved" ? "Open applications" : "Find an opportunity"}{" "}
              <span aria-hidden="true">→</span>
            </Link>
          </section>
        </aside>
      </div>
    </main>
  );
}

export default function Workspace() {
  return (
    <Suspense fallback={<AccountLoading />}>
      <WorkspaceScreen />
    </Suspense>
  );
}
