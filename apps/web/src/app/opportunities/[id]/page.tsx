"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, Opportunity } from "@/lib/api";
export default function Detail() {
  const { id } = useParams<{ id: string }>();
  const [o, setO] = useState<Opportunity | null>(null),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    api<Opportunity>("/opportunities/" + id)
      .then(setO)
      .catch((e) => setError(e.message));
  }, [id]);
  async function action(path: string, body?: object) {
    setBusy(true);
    setMessage("");
    try {
      await api(path, {
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
      });
      setMessage(
        path.endsWith("save")
          ? "Saved to your workspace."
          : "Added to your external application tracker.",
      );
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main" className="detail">
      <Link href="/explore">← Back to opportunities</Link>
      {error ? (
        <p role="alert">{error}</p>
      ) : !o ? (
        <p role="status">Loading opportunity…</p>
      ) : (
        <>
          <div className={"detail-poster " + o.kind.toLowerCase()}>
            <p>{o.organization_name}</p>
            <h1>{o.title}</h1>
            <p>
              {o.kind.toLowerCase()} · {o.location}
            </p>
          </div>
          <div className="detail-grid">
            <article>
              <h2>Make your next move.</h2>
              <p className="description">{o.description}</p>
              <h2>Skills and interests</h2>
              <p>
                {[
                  ...(o.required_skills ?? []),
                  ...(o.preferred_skills ?? []),
                ].join(" · ") || "No specific skills listed."}
              </p>
              <h2>Eligibility</h2>
              <p>
                Published requirements are checked separately from fit. Sign in
                to see your eligibility evidence.
              </p>
              <ul>
                <li>
                  Degrees:{" "}
                  {o.eligibility?.degree_ids
                    ?.map((x) => x.toUpperCase())
                    .join(", ") || "All degrees"}
                </li>
                <li>
                  Branches:{" "}
                  {o.eligibility?.branch_ids
                    ?.map((x) => x.toUpperCase())
                    .join(", ") || "All branches"}
                </li>
                <li>
                  Graduation years:{" "}
                  {o.eligibility?.graduation_years?.join(", ") ||
                    "No restriction listed"}
                </li>
                {Object.entries(o.eligibility?.minimum_cgpa ?? {}).map(
                  ([scale, grade]) => (
                    <li key={scale}>
                      Minimum grade: {grade} on a {scale}-point scale
                    </li>
                  ),
                )}
              </ul>
              <button
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  try {
                    const result = await api<{
                      status: string;
                      reasons: string[];
                    }>("/opportunities/" + id + "/eligibility");
                    setMessage(
                      result.status === "ELIGIBLE"
                        ? "You meet the current eligibility requirements."
                        : result.reasons.join(". "),
                    );
                  } catch (e) {
                    setMessage((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Check my eligibility
              </button>
            </article>
            <aside className="action-panel">
              <p>
                {o.mode === "EXTERNAL"
                  ? "Apply on the organizer’s website"
                  : "Hosted on Alignn"}
              </p>
              <h2>Your next step</h2>
              <p>Registration closes</p>
              <time dateTime={o.registration_closes_at}>
                {new Date(o.registration_closes_at).toLocaleString("en-GB", {
                  timeZone: "UTC",
                })}{" "}
                UTC
              </time>
              {o.mode === "EXTERNAL" && o.apply_url ? (
                <>
                  <a
                    className="button"
                    href={o.apply_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Apply externally ↗
                  </a>
                  <button
                    disabled={busy}
                    onClick={() =>
                      action("/applications", { opportunity_id: o.id })
                    }
                  >
                    Track this application
                  </button>
                </>
              ) : (
                <p>
                  Hosted registration will be available with the Phase 2 event
                  workspace.
                </p>
              )}
              <button
                disabled={busy}
                onClick={() => action("/opportunities/" + id + "/save")}
              >
                Save opportunity
              </button>
              <p role="status">{message}</p>
            </aside>
          </div>
        </>
      )}
    </main>
  );
}
