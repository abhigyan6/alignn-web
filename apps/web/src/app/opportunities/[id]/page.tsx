"use client";
import Link from "next/link";
import { opportunityDate, sourceLabel } from "@/components/opportunity-card";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, Opportunity } from "@/lib/api";
export default function Detail() {
  const { id } = useParams<{ id: string }>();
  const [o, setO] = useState<Opportunity | null>(null),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false),
    [tracked, setTracked] = useState(false);
  const [fit, setFit] = useState<{
    score: number;
    factors: Record<string, number>;
  } | null>(null);
  useEffect(() => {
    window.scrollTo(0, 0);
    const controller = new AbortController();
    setO(null);
    setError("");
    setFit(null);
    setMessage("");
    setTracked(false);
    api<Opportunity>("/opportunities/" + id, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) setO(data);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [id]);
  async function action(path: string, body?: object) {
    setBusy(true);
    setMessage("");
    setTracked(false);
    try {
      await api(path, {
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
      });
      setTracked(path === "/applications");
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
        <div className="detail-placeholder" role="status" aria-busy="true">
          <span className="sr-only">Loading opportunity…</span>
          <span className="skeleton skeleton-heading" aria-hidden="true" />
          <span className="skeleton skeleton-line" aria-hidden="true" />
          <span className="skeleton skeleton-field" aria-hidden="true" />
        </div>
      ) : (
        <>
          <div className="detail-poster">
            <span className={"category-chip " + o.kind.toLowerCase()}>
              {o.kind.toLowerCase()}
            </span>
            <p>{o.organization_name}</p>
            <h1>{o.title}</h1>
            <p>
              {o.kind.toLowerCase()} · {o.location}
            </p>
          </div>
          <div className="detail-grid">
            <aside className="action-panel">
              <p>Apply on the organizer’s website</p>
              <h2>Your next step</h2>
              <p>Applications close</p>
              {o.registration_closes_at ? (
                <time dateTime={o.registration_closes_at}>
                  {opportunityDate(o.registration_closes_at, true)} · IST
                </time>
              ) : (
                <p>No deadline supplied. Check the source for availability.</p>
              )}
              {o.source_name && (
                <p>
                  Source:{" "}
                  <a
                    href={o.source_url ?? o.apply_url ?? "#"}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {sourceLabel(o.source_name)}
                  </a>
                  . Listings may change; confirm details at the source.
                </p>
              )}
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
              <button
                disabled={busy}
                onClick={() => action("/opportunities/" + id + "/save")}
              >
                Save opportunity
              </button>
              <p role="status">{message}</p>
              {tracked && (
                <Link href="/workspace#applications">
                  Open application tracker ↗
                </Link>
              )}
            </aside>
            <article id="opportunity-description">
              <h2>About this opportunity</h2>
              <p className="description">{o.description}</p>
              <h2>Skills and interests</h2>
              <p>
                {[
                  ...(o.required_skills ?? []),
                  ...(o.preferred_skills ?? []),
                ].join(" · ") || "No specific skills listed."}
              </p>
              <button
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  try {
                    setFit(await api("/opportunities/" + id + "/fit"));
                  } catch (e) {
                    setMessage((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                See my profile match
              </button>
              {fit && (
                <section aria-live="polite">
                  <h3>Profile fit: {fit.score}/100</h3>
                  <p>
                    Evidence overlap, not a prediction of selection. Eligibility
                    and location restrictions must be checked separately.
                  </p>
                  <ul>
                    {Object.entries(fit.factors).map(([factor, score]) => (
                      <li key={factor}>
                        {factor.replaceAll("_", " ")}: {Math.round(score)}%
                        overlap
                      </li>
                    ))}
                  </ul>
                </section>
              )}
              <h2>Eligibility</h2>
              {o.source_name ? (
                <p>
                  Eligibility has not been structured for this external listing.
                  Check the full requirements on {sourceLabel(o.source_name)}{" "}
                  before applying.
                </p>
              ) : (
                <>
                  <p>
                    Published requirements are checked separately from fit. Sign
                    in to see your eligibility evidence.
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
                </>
              )}
            </article>
          </div>
        </>
      )}
    </main>
  );
}
