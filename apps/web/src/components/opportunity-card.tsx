"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, Opportunity } from "@/lib/api";
import Icon, { type IconName } from "@/components/icon";

export function sourceLabel(source?: string | null) {
  if (source?.startsWith("Greenhouse:")) return "Employer careers";
  return source || "Alignn catalog";
}
export function opportunityDate(value: string, includeTime = false) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
    ...(includeTime
      ? { hour: "2-digit" as const, minute: "2-digit" as const }
      : {}),
  }).format(new Date(value));
}
export function isClosed(o: Opportunity) {
  const now = Date.now();
  return Boolean(
    (o.status && o.status !== "PUBLISHED") ||
    (o.registration_closes_at &&
      new Date(o.registration_closes_at).getTime() <= now) ||
    (o.ends_at && new Date(o.ends_at).getTime() <= now),
  );
}
export const categoryIcons: Record<string, IconName> = {
  INTERNSHIP: "briefcase",
  JOB: "briefcase",
  HACKATHON: "code",
  COMPETITION: "spark",
  WORKSHOP: "calendar",
  SCHOLARSHIP: "cap",
};

export default function OpportunityCard({
  opportunity: o,
  saved = false,
  savedPending = false,
  onSavedChange,
}: {
  opportunity: Opportunity;
  saved?: boolean;
  /** Saved state is not known yet (session or /me/saved still loading). */
  savedPending?: boolean;
  onSavedChange?: (saved: boolean) => void;
}) {
  const router = useRouter();
  const [isSaved, setSaved] = useState(saved),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => setSaved(saved), [saved]);
  const closed = isClosed(o);
  const category = o.kind.toLowerCase().replaceAll("_", " ");
  const company = o.organization_name.replace(/^Organizer listed on /, "Via ");
  const initials = company
    .replace(/^Via /, "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join("");
  const skills = [
    ...new Set([...(o.required_skills ?? []), ...(o.preferred_skills ?? [])]),
  ].slice(0, 3);
  async function toggleSave() {
    if (busy || savedPending) return;
    setBusy(true);
    setError("");
    try {
      await api(`/opportunities/${o.id}/save`, {
        method: isSaved ? "DELETE" : "POST",
      });
      setSaved(!isSaved);
      onSavedChange?.(!isSaved);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) router.push("/login");
      else setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <article
      className={`event opportunity-card ${closed ? "opportunity-closed" : ""}`}
    >
      <div className="opportunity-card-top">
        <div
          className={`company-monogram ${o.kind.toLowerCase()}`}
          aria-hidden="true"
        >
          {initials}
        </div>
        <div className="card-identity">
          <p className="opportunity-company">{company}</p>
          <span className={`category-label ${o.kind.toLowerCase()}`}>
            <Icon name={categoryIcons[o.kind] ?? "briefcase"} size={14} />
            {category}
          </span>
        </div>
        <button
          className={`bookmark-button ${isSaved && !savedPending ? "is-saved" : ""}`}
          aria-label={
            savedPending
              ? `Checking saved status for ${o.title}`
              : `${isSaved ? "Remove saved" : "Save"} ${o.title}`
          }
          aria-pressed={savedPending ? undefined : isSaved}
          aria-busy={savedPending || busy}
          disabled={busy || savedPending}
          onClick={toggleSave}
        >
          <Icon name="bookmark" />
        </button>
      </div>
      <div className="event-body">
        <h3>
          <Link href={`/opportunities/${o.id}`}>{o.title}</Link>
        </h3>
        <p className="opportunity-location">
          <Icon name="location" size={16} />
          <span>{o.location}</span>
          {o.work_mode !== "UNKNOWN" && (
            <span className="work-mode">{o.work_mode.toLowerCase()}</span>
          )}
        </p>
        {skills.length > 0 && (
          <div className="skill-chips" aria-label="Listed or inferred skills">
            {skills.map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        )}
      </div>
      <div className="event-bottom">
        <span className={closed ? "closed-label" : "deadline-label"}>
          <Icon name="clock" size={15} />
          {closed ? (
            "Closed"
          ) : o.registration_closes_at ? (
            <time dateTime={o.registration_closes_at}>
              Apply by {opportunityDate(o.registration_closes_at)} IST
            </time>
          ) : (
            "Deadline not published"
          )}
        </span>
        <small>{sourceLabel(o.source_name)}</small>
      </div>
      {error && (
        <p className="card-error" role="alert">
          {error}
        </p>
      )}
    </article>
  );
}
