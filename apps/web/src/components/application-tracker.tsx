"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import type { components } from "../../../../packages/api-client/src/schema";
import { api } from "@/lib/api";
import styles from "./workspace.module.css";

type EventInput = components["schemas"]["ApplicationEventCreate"];
type Stage = EventInput["status"];
type Application = {
  id: string;
  opportunity_id: string;
  title: string;
  organization_name: string;
  status: Stage;
  created_at?: string;
  registration_closes_at?: string | null;
};
type HistoryEntry = { status: Stage; note: string; created_at: string };
const stageLabels: Record<Stage, string> = {
  SAVED: "Saved",
  APPLIED: "Applied",
  INTERVIEW: "Interview",
  OFFER: "Offer",
  REJECTED: "Rejected",
  WITHDRAWN: "Withdrawn",
};

function formatDate(value: string, includeTime = false) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
    ...(includeTime ? ({ hour: "2-digit", minute: "2-digit" } as const) : {}),
  }).format(new Date(value));
}

function ApplicationRow({
  application,
  onUpdated,
}: {
  application: Application;
  onUpdated: (updated: Application) => void;
}) {
  const [open, setOpen] = useState(false);
  const [stage, setStage] = useState(application.status);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [saveError, setSaveError] = useState("");
  const [history, setHistory] = useState<HistoryEntry[] | null>(null);
  const [historyError, setHistoryError] = useState("");
  const [revision, setRevision] = useState(0);
  const eventsPath = "/applications/" + application.id + "/events";

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setHistoryError("");
    api<{ items: HistoryEntry[] }>(eventsPath, { signal: controller.signal })
      .then((result) => {
        if (!controller.signal.aborted) setHistory(result.items);
      })
      .catch((error: Error) => {
        if (!controller.signal.aborted) setHistoryError(error.message);
      });
    return () => controller.abort();
  }, [eventsPath, open, revision]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setNotice("");
    setSaveError("");
    try {
      const updated = await api<Application>(eventsPath, {
        method: "POST",
        body: JSON.stringify({
          status: stage,
          note: note.trim(),
        } satisfies EventInput),
      });
      onUpdated(updated);
      setStage(updated.status);
      setNote("");
      setNotice("Application update saved.");
      setHistoryError("");
      setRevision((value) => value + 1);
    } catch (error) {
      setSaveError((error as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <li className={styles.applicationRow}>
      <div className={styles.applicationSummary}>
        <span className={styles.companyInitial} aria-hidden="true">
          {application.organization_name.trim().slice(0, 1).toUpperCase()}
        </span>
        <div className={styles.applicationIdentity}>
          <Link href={"/opportunities/" + application.opportunity_id}>
            {application.title}
          </Link>
          <p>{application.organization_name}</p>
          {application.created_at && (
            <p className={styles.addedDate}>
              Added{" "}
              <time dateTime={application.created_at}>
                {formatDate(application.created_at)}
              </time>
            </p>
          )}
        </div>
        <span className={styles.stageBadge} data-stage={application.status}>
          {stageLabels[application.status]}
        </span>
        <button
          className={styles.manageButton}
          type="button"
          disabled={saving}
          aria-expanded={open}
          aria-controls={"application-" + application.id}
          aria-label={(open ? "Close " : "Manage ") + application.title}
          onClick={() => {
            setHistoryError("");
            setOpen(!open);
          }}
        >
          {open ? "Close" : "Update"}
          <span aria-hidden="true">{open ? "−" : "+"}</span>
        </button>
      </div>
      <div id={"application-" + application.id} hidden={!open}>
        {open && (
          <div className={styles.applicationDetails}>
            <form className={styles.updateForm} onSubmit={save}>
              <div className={styles.formHeading}>
                <h3>Update your progress</h3>
                <p>
                  Record what happened on the original platform or with the
                  organizer.
                </p>
              </div>
              <label>
                Application stage
                <select
                  value={stage}
                  disabled={saving}
                  onChange={(event) => setStage(event.target.value as Stage)}
                >
                  {Object.entries(stageLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <p className={styles.fieldHint}>
                {stage === "SAVED"
                  ? "Saved means you haven’t submitted an application yet."
                  : stage === "APPLIED"
                    ? "Use Applied after you submit on the original website."
                    : "Choose the stage that reflects your latest update."}
              </p>
              <label>
                Private note <span className={styles.optional}>(optional)</span>
                <textarea
                  value={note}
                  maxLength={2000}
                  rows={3}
                  disabled={saving}
                  placeholder="A useful detail to remember for your next step…"
                  onChange={(event) => setNote(event.target.value)}
                />
              </label>
              <div className={styles.updateActions}>
                <button
                  className="button"
                  disabled={
                    saving || (stage === application.status && !note.trim())
                  }
                >
                  {saving ? "Saving…" : "Save update"}
                </button>
                <span>Only you can see these notes.</span>
              </div>
              {notice && (
                <p className={styles.successMessage} role="status">
                  {notice}
                </p>
              )}
              {saveError && (
                <p className={styles.errorMessage} role="alert">
                  {saveError}
                </p>
              )}
            </form>
            <section
              className={styles.historyPanel}
              aria-labelledby={"history-" + application.id}
            >
              <h3 id={"history-" + application.id}>Application history</h3>
              {historyError ? (
                <div>
                  <p role="alert" className={styles.errorMessage}>
                    {historyError}
                  </p>
                  <button
                    type="button"
                    className={styles.textButton}
                    onClick={() => {
                      setHistoryError("");
                      setRevision((value) => value + 1);
                    }}
                  >
                    Retry history
                  </button>
                </div>
              ) : !history ? (
                <p role="status" className={styles.fieldHint}>
                  Loading history…
                </p>
              ) : history.length ? (
                <ol className={styles.historyList}>
                  {history.map((entry, index) => (
                    <li key={entry.created_at + "-" + index}>
                      <span className={styles.historyDot} aria-hidden="true" />
                      <strong>{stageLabels[entry.status]}</strong>
                      <time dateTime={entry.created_at}>
                        {formatDate(entry.created_at, true)} · IST
                      </time>
                      {entry.note && <p>{entry.note}</p>}
                    </li>
                  ))}
                </ol>
              ) : (
                <p className={styles.fieldHint}>
                  Your updates will appear here.
                </p>
              )}
            </section>
          </div>
        )}
      </div>
    </li>
  );
}

export default function ApplicationTracker() {
  const [items, setItems] = useState<Application[] | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [filter, setFilter] = useState<Stage | "ALL">("ALL");
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    api<{ items: Application[] }>("/me/applications", {
      signal: controller.signal,
    })
      .then((result) => {
        if (!controller.signal.aborted) setItems(result.items);
      })
      .catch((failure: Error) => {
        if (!controller.signal.aborted) setError(failure.message);
      });
    return () => controller.abort();
  }, [attempt]);
  const query = search.trim().toLocaleLowerCase();
  const shown = (items ?? []).filter(
    (item) =>
      (filter === "ALL" || item.status === filter) &&
      (!query ||
        (item.title + " " + item.organization_name)
          .toLocaleLowerCase()
          .includes(query)),
  );

  return (
    <section
      id="applications"
      aria-labelledby="application-tracker-title"
      className={styles.tracker}
    >
      <div className={styles.sectionToolbar}>
        <div>
          <h2 id="application-tracker-title">
            Application tracker{items && <span>{items.length}</span>}
          </h2>
          <p className={styles.trackerIntro}>
            Your records, updated by you. Tracking doesn’t send an application.
          </p>
        </div>
      </div>
      {error ? (
        <div className={styles.filteredEmpty}>
          <h3>Unable to load applications</h3>
          <p role="alert">{error}</p>
          <button
            type="button"
            className="button secondary"
            onClick={() => setAttempt((value) => value + 1)}
          >
            Try again
          </button>
        </div>
      ) : !items ? (
        <div role="status" aria-busy="true" className={styles.trackerLoading}>
          <span className="sr-only">Loading applications…</span>
          {[0, 1, 2].map((n) => (
            <div aria-hidden="true" key={n}>
              <span />
              <span />
              <span />
            </div>
          ))}
        </div>
      ) : !items.length ? (
        <div className={styles.emptyState}>
          <span className={styles.emptyIcon} aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <path d="M8 7h16v21H8zM12 4h8v6h-8zM12 16h8M12 21h5" />
            </svg>
          </span>
          <p className={styles.kicker}>From saved to your next step</p>
          <h3>No applications tracked yet.</h3>
          <p>
            When you find something worth applying to, choose “Track
            application” on its details page. Update its stage after you apply
            at the source.
          </p>
          <Link className="button" href="/explore">
            Discover opportunities <span aria-hidden="true">↗</span>
          </Link>
        </div>
      ) : (
        <>
          <div className={styles.trackerControls}>
            <label className={styles.searchControl}>
              <span className="sr-only">Search applications</span>
              <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
                <circle cx="8.5" cy="8.5" r="5.5" />
                <path d="m13 13 4 4" />
              </svg>
              <input
                type="search"
                placeholder="Search a role or organizer"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>
            <label className={styles.stageFilter}>
              Stage
              <select
                value={filter}
                onChange={(event) =>
                  setFilter(event.target.value as Stage | "ALL")
                }
              >
                <option value="ALL">All stages</option>
                {Object.entries(stageLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <p className={styles.liveNotice} role="status">
            {notice}
          </p>
          <p className={styles.resultsLabel}>
            {shown.length} {shown.length === 1 ? "record" : "records"}
            {filter !== "ALL" ? ` · ${stageLabels[filter]}` : ""}
          </p>
          {shown.length ? (
            <ul className={styles.applicationList}>
              {shown.map((application) => (
                <ApplicationRow
                  key={application.id}
                  application={application}
                  onUpdated={(updated) => {
                    setItems(
                      (current) =>
                        current?.map((item) =>
                          item.id === updated.id ? updated : item,
                        ) ?? [],
                    );
                    if (filter !== "ALL" && filter !== updated.status) {
                      setFilter("ALL");
                      setNotice(
                        `Application updated to ${stageLabels[updated.status]}. Showing all stages.`,
                      );
                    } else setNotice("");
                  }}
                />
              ))}
            </ul>
          ) : (
            <div className={styles.filteredEmpty}>
              <h3>No applications match this view.</h3>
              <p>Try another search or show all stages.</p>
              <button
                className="button secondary"
                type="button"
                onClick={() => {
                  setSearch("");
                  setFilter("ALL");
                }}
              >
                Clear filters
              </button>
            </div>
          )}
          {items.length >= 100 && (
            <p className={styles.collectionNote}>
              Showing up to 100 recent application records.
            </p>
          )}
        </>
      )}
    </section>
  );
}
