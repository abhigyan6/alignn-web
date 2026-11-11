import Link from "next/link";
import { Opportunity } from "@/lib/api";

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

export default function OpportunityCard({
  opportunity: o,
}: {
  opportunity: Opportunity;
}) {
  const category = o.kind.toLowerCase().replaceAll("_", " ");
  return (
    <Link className="event opportunity-card" href={"/opportunities/" + o.id}>
      <div className="opportunity-card-top">
        <span className={"category-chip " + o.kind.toLowerCase()}>
          {category}
        </span>
        <span className="card-arrow" aria-hidden="true">
          ↗
        </span>
      </div>
      <div className="event-body">
        <p className="opportunity-company">{o.organization_name}</p>
        <h3>{o.title}</h3>
        <p className="opportunity-location">
          {o.location}
          <span aria-hidden="true"> · </span>
          {o.work_mode === "UNKNOWN"
            ? "Work mode not specified"
            : o.work_mode.toLowerCase()}
        </p>
        <div className="skill-chips" aria-label="Listed or inferred skills">
          {(o.preferred_skills ?? []).slice(0, 3).map((skill) => (
            <span key={skill}>{skill}</span>
          ))}
        </div>
      </div>
      <div className="event-bottom">
        {o.registration_closes_at ? (
          <time dateTime={o.registration_closes_at}>
            Apply by {opportunityDate(o.registration_closes_at)} · IST
          </time>
        ) : (
          <span>Deadline not published</span>
        )}
        <small>{sourceLabel(o.source_name)}</small>
      </div>
    </Link>
  );
}
