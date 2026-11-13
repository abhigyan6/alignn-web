"use client";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api, Opportunity } from "@/lib/api";
import { useSavedIds } from "@/lib/saved-ids";
import SavedStatusNote from "@/components/saved-status-note";
import Icon, { BrandMark } from "@/components/icon";
import OpportunityCard, { sourceLabel } from "@/components/opportunity-card";
import OpportunitySkeleton from "@/components/opportunity-skeleton";

export default function Landing() {
  const router = useRouter();
  const [items, setItems] = useState<Opportunity[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(false),
    [query, setQuery] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    api<{ items: Opportunity[] }>("/opportunities?sort=deadline&limit=3", {
      signal: controller.signal,
    })
      .then((data) => setItems(data.items))
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);
  const saved = useSavedIds();
  const savedPending = saved.status !== "ready";
  function search(e: FormEvent) {
    e.preventDefault();
    router.push(
      `/explore${query.trim() ? "?q=" + encodeURIComponent(query.trim()) : ""}`,
    );
  }
  return (
    <main id="main" className="home-page">
      <section className="landing-hero">
        <div className="landing-copy">
          <p className="landing-audience">
            <span>For the student figuring out what’s next.</span>
          </p>
          <h1>
            Find opportunities.
            <br />
            Find your direction.
          </h1>
          <p className="landing-intro">
            Internships, hackathons and events across India. A place to discover
            what fits your interests and turn it into your next step.
          </p>
          <form className="search home-search" role="search" onSubmit={search}>
            <Icon name="search" />
            <label htmlFor="home-search" className="sr-only">
              Search opportunities
            </label>
            <input
              id="home-search"
              type="search"
              placeholder="What do you want to explore?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button className="button" aria-label="Explore opportunities">
              <Icon name="arrow" />
            </button>
          </form>
          <div className="popular-searches">
            <span>Start with</span>
            <Link href="/explore?kind=INTERNSHIP">Internships</Link>
            <Link href="/explore?kind=HACKATHON">Hackathons</Link>
            <Link href="/explore?kind=WORKSHOP">Workshops</Link>
          </div>
          <div className="landing-profile-link">
            <Icon name="user" size={17} />
            <Link href="/signup">
              Create a profile for recommendations that start with you
            </Link>
          </div>
        </div>
        <div className="landing-visual">
          <div className="opportunity-desk">
            <div className="desk-title">
              <span className="desk-mark">
                <BrandMark />
              </span>
              <span>
                <strong>There’s more than one way forward.</strong>
                <span>A few opportunities to explore</span>
              </span>
            </div>
            <div className="desk-list">
              {loading ? (
                <div className="desk-loading" role="status">
                  Finding opportunities…
                </div>
              ) : items.length ? (
                items.map((o) => (
                  <Link
                    className="desk-opportunity"
                    href={`/opportunities/${o.id}`}
                    key={o.id}
                  >
                    <span className={`desk-category ${o.kind.toLowerCase()}`}>
                      <Icon
                        name={
                          o.kind === "HACKATHON"
                            ? "code"
                            : o.kind === "WORKSHOP"
                              ? "calendar"
                              : "briefcase"
                        }
                        size={22}
                      />
                    </span>
                    <span>
                      <small>{sourceLabel(o.source_name)}</small>
                      <strong>{o.title}</strong>
                      <span>{o.location}</span>
                    </span>
                    <Icon name="chevron" size={17} />
                  </Link>
                ))
              ) : (
                <p className="desk-loading">
                  {error
                    ? "The feed is taking a moment. Browse opportunities to try again."
                    : "New opportunities will appear here as sources refresh."}
                </p>
              )}
            </div>
            <div className="desk-footer">
              <span>Discover across platforms</span>
              <Link href="/explore">
                Explore the feed
                <Icon name="arrow" size={15} />
              </Link>
            </div>
          </div>
          <div className="profile-tag">
            <span className="profile-tag-icon">
              <Icon name="check" size={16} />
            </span>
            <span>
              Your interests.
              <br />
              <strong>A more relevant starting point.</strong>
            </span>
          </div>
        </div>
      </section>
      <section className="opportunity-paths" aria-label="Ways to explore">
        <Link href="/explore?kind=INTERNSHIP">
          <span className="path-icon internships">
            <Icon name="briefcase" size={24} />
          </span>
          <span>
            <strong>Get experience</strong>
            <span>Explore internships and early career roles</span>
          </span>
          <Icon name="arrow" />
        </Link>
        <Link href="/explore?kind=HACKATHON">
          <span className="path-icon hackathons">
            <Icon name="code" size={24} />
          </span>
          <span>
            <strong>Build something</strong>
            <span>Find hackathons and coding challenges</span>
          </span>
          <Icon name="arrow" />
        </Link>
        <Link href="/explore?kind=WORKSHOP">
          <span className="path-icon workshops">
            <Icon name="calendar" size={24} />
          </span>
          <span>
            <strong>Follow your interests</strong>
            <span>Discover workshops and technical events</span>
          </span>
          <Icon name="arrow" />
        </Link>
      </section>
      <section
        className="home-opportunities"
        aria-labelledby="home-opportunities-title"
      >
        <div className="section-heading">
          <div>
            <h2 id="home-opportunities-title">A few places to start.</h2>
            <p>Real opportunities, connected to their original sources.</p>
          </div>
          <Link className="text-link" href="/explore">
            View all opportunities
            <Icon name="arrow" size={17} />
          </Link>
        </div>
        {loading ? (
          <OpportunitySkeleton />
        ) : items.length ? (
          <>
            {saved.status === "unknown" && (
              <SavedStatusNote onRetry={saved.retry} />
            )}
            <div className="event-grid home-event-grid">
              {items.map((o) => (
                <OpportunityCard
                  key={o.id}
                  opportunity={o}
                  saved={saved.ids.has(o.id)}
                  savedPending={savedPending}
                  onSavedChange={(value) => saved.setSaved(o.id, value)}
                />
              ))}
            </div>
          </>
        ) : (
          <div className="empty">
            <p>
              {error
                ? "Unable to load the preview. Open discovery to try again."
                : "There are no active opportunities to preview yet."}
            </p>
            <Link className="button secondary" href="/explore">
              Open discovery
            </Link>
          </div>
        )}
      </section>
      <section className="profile-explainer">
        <div className="profile-explainer-copy">
          <h2>
            Less starting from scratch.
            <br />
            More finding your fit.
          </h2>
          <p>
            Add your education, interests and skills to put more relevant
            opportunities first. Your profile stays yours to review and update.
          </p>
          <Link className="button" href="/onboarding?edit=1">
            Build your profile
            <Icon name="arrow" size={18} />
          </Link>
        </div>
        <div className="journey-list">
          <div>
            <span>
              <Icon name="user" size={22} />
            </span>
            <div>
              <h3>Start with what you know</h3>
              <p>
                Add your skills and what you’d like to explore. Your résumé is
                optional.
              </p>
            </div>
          </div>
          <div>
            <span>
              <Icon name="search" size={22} />
            </span>
            <div>
              <h3>See what connects</h3>
              <p>
                Browse profile-based recommendations and inspect the match
                before deciding.
              </p>
            </div>
          </div>
          <div>
            <span>
              <Icon name="bookmark" size={22} />
            </span>
            <div>
              <h3>Keep your next steps together</h3>
              <p>
                Save a shortlist, apply at the source and record your
                application progress.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
