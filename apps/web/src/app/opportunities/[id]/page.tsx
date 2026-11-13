"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError, Opportunity } from "@/lib/api";
import { useSessionReady } from "@/lib/session-readiness";
import { useSavedIds } from "@/lib/saved-ids";
import SavedStatusNote from "@/components/saved-status-note";
import {
  categoryIcons,
  isClosed,
  opportunityDate,
  sourceLabel,
} from "@/components/opportunity-card";
import Icon from "@/components/icon";
import BrandLoader from "@/components/brand-loader";

const factorNames: Record<string, string> = {
  technical: "Skills",
  projects: "Projects",
  interests: "Interests",
  work_mode: "Work preference",
  location: "Location preference",
};
export default function Detail() {
  const { id } = useParams<{ id: string }>();
  const [o, setO] = useState<Opportunity | null>(null),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false),
    [tracked, setTracked] = useState(false),
    [attempt, setAttempt] = useState(0),
    [needsSignIn, setNeedsSignIn] = useState(false);
  const sessionReady = useSessionReady();
  const savedIds = useSavedIds();
  const saved = savedIds.ids.has(id);
  const savedKnown = savedIds.status === "ready";
  const [feedbackFor, setFeedbackFor] = useState<
    "save" | "track" | "fit" | null
  >(null);
  const [fit, setFit] = useState<{
    score: number;
    factors: Record<string, number>;
  } | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setO(null);
    setError("");
    setFit(null);
    setMessage("");
    setTracked(false);
    setNeedsSignIn(false);
    setFeedbackFor(null);
    api<Opportunity>(`/opportunities/${id}`, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) setO(data);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [id, attempt]);
  async function action(kind: "save" | "track" | "fit") {
    if (!o || busy || !sessionReady) return;
    if (kind === "save" && !savedKnown) return;
    setBusy(true);
    setMessage("");
    setNeedsSignIn(false);
    setFeedbackFor(kind);
    try {
      if (kind === "fit") setFit(await api(`/opportunities/${id}/fit`));
      else if (kind === "save") {
        await api(`/opportunities/${id}/save`, {
          method: saved ? "DELETE" : "POST",
        });
        savedIds.setSaved(id, !saved);
        setMessage(saved ? "Removed from Saved." : "Added to Saved.");
      } else {
        await api("/applications", {
          method: "POST",
          body: JSON.stringify({ opportunity_id: id }),
        });
        setTracked(true);
        setMessage(
          "Added to Applications. Update its progress after you apply.",
        );
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setNeedsSignIn(true);
        setMessage(
          "Sign in to save opportunities, see your fit or track applications.",
        );
      } else setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const closed = o ? isClosed(o) : false;
  return (
    <main id="main" className="detail">
      <Link className="back-link" href="/explore">
        <Icon name="arrow" size={16} style={{ transform: "rotate(180deg)" }} />
        Back to opportunities
      </Link>
      {error ? (
        <div className="feedback error-feedback" role="alert">
          <div>
            <h1>Unable to open this opportunity.</h1>
            <p>{error}</p>
          </div>
          <button onClick={() => setAttempt((v) => v + 1)}>Try again</button>
        </div>
      ) : !o ? (
        <div className="empty" role="status" aria-busy="true">
          <BrandLoader />
          <p>Loading opportunity…</p>
        </div>
      ) : (
        <>
          <header className="detail-header">
            <div className="detail-labels">
              <span className={`category-chip ${o.kind.toLowerCase()}`}>
                <Icon name={categoryIcons[o.kind] ?? "briefcase"} size={16} />
                {o.kind.toLowerCase()}
              </span>
              <span>{o.organization_name}</span>
              {closed && <span className="closed-label">Closed</span>}
            </div>
            <h1>{o.title}</h1>
            <div className="detail-facts">
              <span>
                <Icon name="location" size={17} />
                {o.location}
              </span>
              <span>
                <Icon name="globe" size={17} />
                {o.work_mode === "UNKNOWN"
                  ? "Format not specified"
                  : o.work_mode.toLowerCase()}
              </span>
              {o.starts_at && (
                <span>
                  <Icon name="calendar" size={17} />
                  {opportunityDate(o.starts_at)}
                  {o.ends_at && ` – ${opportunityDate(o.ends_at)}`}
                </span>
              )}
            </div>
          </header>
          <div className="detail-grid">
            <article className="detail-article">
              <section id="opportunity-description">
                <h2>About this opportunity</h2>
                <p className="description">{o.description}</p>
              </section>
              <section>
                <h2>Skills and interests</h2>
                {[...(o.required_skills ?? []), ...(o.preferred_skills ?? [])]
                  .length ? (
                  <>
                    <div className="skill-chips">
                      {[
                        ...new Set([
                          ...(o.required_skills ?? []),
                          ...(o.preferred_skills ?? []),
                        ]),
                      ].map((skill) => (
                        <span key={skill}>{skill}</span>
                      ))}
                    </div>
                    <p>
                      Skills may be listed by the source or inferred from its
                      description. They are not confirmed eligibility
                      requirements.
                    </p>
                  </>
                ) : (
                  <p>
                    The source hasn’t supplied structured skill requirements.
                    Review the description for details.
                  </p>
                )}
              </section>
              <section>
                <h2>How it connects to your profile</h2>
                <p>
                  See the overlap with your confirmed skills, projects and
                  preferences. A profile fit score is a starting point, not a
                  prediction of selection.
                </p>
                <button
                  className="button secondary"
                  disabled={busy || !sessionReady}
                  onClick={() => action("fit")}
                >
                  <Icon name="user" size={18} />
                  See my profile match
                </button>
                {feedbackFor === "fit" && message && (
                  <div className="fit-feedback" role="status">
                    <p>{message}</p>
                    {needsSignIn && (
                      <Link className="text-link" href="/login">
                        Sign in to see your fit
                        <Icon name="arrow" size={16} />
                      </Link>
                    )}
                  </div>
                )}
                {fit && (
                  <div className="fit-summary" aria-live="polite">
                    <h3>Profile fit: {Math.round(fit.score)}/100</h3>
                    <ul className="fit-factors">
                      {Object.entries(fit.factors).map(([factor, value]) => (
                        <li key={factor}>
                          <span>
                            {factorNames[factor] ?? factor.replaceAll("_", " ")}
                          </span>
                          <span>{Math.round(value)}% overlap</span>
                        </li>
                      ))}
                    </ul>
                    <Link className="text-link" href="/onboarding?edit=1">
                      Review your profile
                      <Icon name="arrow" size={16} />
                    </Link>
                  </div>
                )}
              </section>
              <section>
                <h2>Before you apply</h2>
                <p>
                  Availability, eligibility and application steps are managed by
                  the original organizer or employer. Check the latest
                  requirements on {sourceLabel(o.source_name)}. An India-based
                  listing may still have specific audience restrictions.
                </p>
                {o.source_checked_at && (
                  <p>
                    Last checked {opportunityDate(o.source_checked_at, true)}{" "}
                    IST.
                  </p>
                )}
                <a
                  className="text-link"
                  href={o.source_url ?? o.apply_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Read the original listing
                  <Icon name="external" size={16} />
                </a>
              </section>
            </article>
            <aside className="action-panel" aria-label="Opportunity actions">
              {closed && (
                <div className="closed-notice">
                  <strong>This opportunity is closed.</strong>
                  <br />
                  You can keep it in your history and review the original
                  source.
                </div>
              )}
              <h2>{closed ? "Keep your record" : "Interested in this one?"}</h2>
              <p className="action-note">
                {closed
                  ? "Saved details stay available for your reference."
                  : "Apply through the original platform, then keep track of your progress here."}
              </p>
              <dl>
                <dt>Registration deadline</dt>
                <dd>
                  {o.registration_closes_at ? (
                    <time dateTime={o.registration_closes_at}>
                      {opportunityDate(o.registration_closes_at, true)} IST
                    </time>
                  ) : (
                    "Not published by the source"
                  )}
                </dd>
                <dt>Original source</dt>
                <dd>{sourceLabel(o.source_name)}</dd>
              </dl>
              {!closed && (
                <a
                  className="button"
                  href={o.apply_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Apply on {sourceLabel(o.source_name)}
                  <Icon name="external" size={17} />
                </a>
              )}
              {savedIds.status === "unknown" && (
                <SavedStatusNote onRetry={savedIds.retry} />
              )}
              <button
                className="button outline"
                aria-pressed={saved}
                disabled={busy || !sessionReady || !savedKnown}
                aria-busy={!sessionReady || !savedKnown}
                onClick={() => action("save")}
              >
                <Icon name={saved ? "check" : "bookmark"} size={18} />
                {saved ? "Saved" : "Save opportunity"}
              </button>
              {!closed && (
                <button
                  className="text-button"
                  disabled={busy || tracked || !sessionReady}
                  onClick={() => action("track")}
                >
                  <Icon name="briefcase" size={17} />
                  {tracked ? "Added to Applications" : "Track this application"}
                </button>
              )}
              <p className="action-note">
                Saving or tracking a listing does not submit an application.
              </p>
              {feedbackFor !== "fit" && message && (
                <p className="action-status" role="status">
                  {message}
                </p>
              )}
              {feedbackFor !== "fit" && needsSignIn && (
                <Link className="text-link" href="/login">
                  Sign in to continue
                  <Icon name="arrow" size={16} />
                </Link>
              )}
              {tracked && (
                <Link className="text-link" href="/workspace?tab=applications">
                  Open Applications
                  <Icon name="arrow" size={16} />
                </Link>
              )}
            </aside>
          </div>
        </>
      )}
    </main>
  );
}
