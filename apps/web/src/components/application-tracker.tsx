"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import type { components } from "../../../../packages/api-client/src/schema";
import { api } from "@/lib/api";

type EventInput = components["schemas"]["ApplicationEventCreate"];
type Stage = EventInput["status"];
type Application = {
  id: string;
  opportunity_id: string;
  title: string;
  organization_name: string;
  status: Stage;
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

function ApplicationRow({ application }: { application: Application }) {
  const [current, setCurrent] = useState(application);
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
    const input: EventInput = { status: stage, note: note.trim() };
    setSaving(true);
    setNotice("");
    setSaveError("");
    try {
      const updated = await api<Application>(eventsPath, {
        method: "POST",
        body: JSON.stringify(input),
      });
      setCurrent(updated);
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
    <li className="tracker-row">
      <div className="tracker-summary">
        <div>
          <Link href={"/opportunities/" + current.opportunity_id}>
            <strong>{current.title}</strong>
          </Link>
          <p>
            {current.organization_name} · {stageLabels[current.status]}
          </p>
        </div>
        <button
          type="button"
          disabled={saving}
          aria-expanded={open}
          aria-controls={"application-" + current.id}
          aria-label={(open ? "Close " : "Manage ") + current.title}
          onClick={() => {
            setHistoryError("");
            setOpen(!open);
          }}
        >
          {open ? "Close" : "Manage"}
        </button>
      </div>
      <div id={"application-" + current.id} hidden={!open}>
        {open && (
          <>
            <form className="tracker-form" onSubmit={save}>
              <label>
                Stage
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
              <label>
                Private note (optional)
                <textarea
                  value={note}
                  maxLength={2000}
                  rows={3}
                  disabled={saving}
                  onChange={(event) => setNote(event.target.value)}
                />
              </label>
              <button
                className="button"
                disabled={saving || (stage === current.status && !note.trim())}
              >
                {saving ? "Saving…" : "Save update"}
              </button>
            </form>
            {notice && <p role="status">{notice}</p>}
            {saveError && <p role="alert">{saveError}</p>}
            <h3>Application history</h3>
            {historyError ? (
              <div>
                <p role="alert">{historyError}</p>
                <button
                  type="button"
                  onClick={() => {
                    setHistoryError("");
                    setRevision((value) => value + 1);
                  }}
                >
                  Retry history
                </button>
              </div>
            ) : !history ? (
              <p role="status">Loading history…</p>
            ) : history.length ? (
              <ol className="tracker-history">
                {history.map((entry, index) => (
                  <li key={entry.created_at + "-" + index}>
                    <strong>{stageLabels[entry.status]}</strong>{" "}
                    <time dateTime={entry.created_at}>
                      {new Intl.DateTimeFormat(undefined, {
                        dateStyle: "medium",
                        timeStyle: "short",
                      }).format(new Date(entry.created_at))}
                    </time>
                    {entry.note && <p>{entry.note}</p>}
                  </li>
                ))}
              </ol>
            ) : (
              <p>No updates recorded yet.</p>
            )}
          </>
        )}
      </div>
    </li>
  );
}

export default function ApplicationTracker() {
  const [items, setItems] = useState<Application[] | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
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

  return (
    <section id="applications" aria-labelledby="application-tracker-title">
      <h2 id="application-tracker-title">Application tracker</h2>
      <p>Keep track of applications you make on other sites.</p>
      {error ? (
        <div className="empty">
          <p role="alert">{error}</p>
          <button
            type="button"
            onClick={() => {
              setError("");
              setAttempt((value) => value + 1);
            }}
          >
            Retry applications
          </button>
        </div>
      ) : !items ? (
        <p role="status">Loading applications…</p>
      ) : items.length ? (
        <ul className="tracker-list">
          {items.map((application) => (
            <ApplicationRow key={application.id} application={application} />
          ))}
        </ul>
      ) : (
        <div className="empty">
          <h3>No tracked applications yet.</h3>
          <p>
            Choose “Track this application” on an external listing to add it
            here.
          </p>
          <Link href="/explore">Explore opportunities ↗</Link>
        </div>
      )}
    </section>
  );
}
