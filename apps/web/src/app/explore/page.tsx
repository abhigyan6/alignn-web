"use client";
import OpportunitySkeleton from "@/components/opportunity-skeleton";
import Link from "next/link";
import { useEffect, useState, FormEvent } from "react";
import { api, Opportunity } from "@/lib/api";
const categories = [
  ["", "Everything"],
  ["INTERNSHIP", "Internships"],
  ["JOB", "Jobs"],
  ["HACKATHON", "Hackathons"],
  ["COMPETITION", "Competitions"],
  ["WORKSHOP", "Workshops"],
];
export default function Explore() {
  const [kind, setKind] = useState(""),
    [query, setQuery] = useState(""),
    [search, setSearch] = useState(""),
    [sort, setSort] = useState("match");
  const [items, setItems] = useState<Opportunity[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [rank, setRank] = useState(""),
    [next, setNext] = useState<number | null>(null),
    [cursor, setCursor] = useState(0),
    [attempt, setAttempt] = useState(0),
    [polls, setPolls] = useState(0);
  useEffect(() => {
    setPolls(0);
  }, [kind, search, sort]);
  useEffect(() => {
    if (rank !== "PENDING" || sort !== "match" || polls >= 6) return;
    const timer = setTimeout(() => {
      setPolls((value) => value + 1);
      setAttempt((value) => value + 1);
    }, 5000);
    return () => clearTimeout(timer);
  }, [rank, sort, attempt, polls]);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError("");
    const params = new URLSearchParams({
      q: search,
      sort,
      cursor: String(cursor),
      limit: "12",
    });
    if (kind) params.set("kind", kind);
    api<{
      items: Opportunity[];
      ranking_status: string;
      next_cursor: number | null;
    }>("/opportunities?" + params, { signal: controller.signal })
      .then((data) => {
        if (active) {
          setItems(data.items);
          setRank(data.ranking_status);
          setNext(data.next_cursor);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [kind, search, sort, cursor, attempt]);
  function submit(e: FormEvent) {
    e.preventDefault();
    setCursor(0);
    setSearch(query);
  }
  return (
    <main id="main">
      <section className="hero">
        <div>
          <h1>
            Find your people.
            <br />
            Build your next chapter.
          </h1>
          <p>
            Discover work worth doing, challenges worth taking and the
            opportunities that move you forward.
          </p>
          <form role="search" onSubmit={submit} className="search">
            <label className="sr-only" htmlFor="search">
              Search opportunities
            </label>
            <input
              id="search"
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search a role, skill or opportunity"
            />
            <button className="button">Find opportunities</button>
          </form>
        </div>
        <div className="loop-art" aria-hidden="true">
          <i />
          <i />
          <span>
            Good things
            <br />
            happen together.
          </span>
        </div>
      </section>
      <div className="category-bar" aria-label="Opportunity categories">
        {categories.map(([value, label]) => (
          <button
            key={value}
            aria-pressed={kind === value}
            onClick={() => {
              setCursor(0);
              setKind(value);
            }}
          >
            {label}
          </button>
        ))}
      </div>
      <section className="marketplace">
        <aside className="editorial">
          <h2>
            A little direction.
            <br />A lot of possibility.
          </h2>
          <p>
            Explore by what interests you. Save the ones that matter, then keep
            your next steps in one place.
          </p>
          <Link href="/workspace">Open your workspace ↗</Link>
          <div className="tip">
            <h3>Fit is a starting point.</h3>
            <p>
              Match scores explain profile overlap. Eligibility is checked
              separately against the published requirements.
            </p>
          </div>
        </aside>
        <div className="results">
          <div className="section-heading">
            <div>
              <h2>
                {search
                  ? "Results for “" + search + "”"
                  : "Your next opportunity"}
              </h2>
              <p>Published opportunities from the Alignn catalog.</p>
            </div>
            <label>
              Sort by
              <select
                value={sort}
                onChange={(e) => {
                  setCursor(0);
                  setSort(e.target.value);
                }}
              >
                <option value="deadline">Closing soon</option>
                <option value="newest">Newest</option>
                <option value="match">My match</option>
              </select>
            </label>
          </div>
          {rank === "PENDING" && polls < 6 && (
            <p role="status">
              Your match ranking is being calculated. Showing newest
              opportunities for now.
            </p>
          )}
          {(rank === "UNAVAILABLE" || (rank === "PENDING" && polls >= 6)) && (
            <p role="status">
              Matching is temporarily unavailable. Showing newest opportunities.{" "}
              <button
                type="button"
                onClick={() => {
                  setPolls(0);
                  setAttempt((value) => value + 1);
                }}
              >
                Check ranking again
              </button>
            </p>
          )}
          {rank === "SIGN_IN_REQUIRED" && (
            <p>
              <Link href="/login">Sign in</Link> for personalized matching.
              Showing newest opportunities.
            </p>
          )}
          {error ? (
            <div className="empty" role="alert">
              <h3>We couldn’t load opportunities.</h3>
              <p>{error}</p>
              <button onClick={() => setAttempt(attempt + 1)}>Try again</button>
            </div>
          ) : loading ? (
            <OpportunitySkeleton />
          ) : items.length ? (
            <div className="event-grid">
              {items.map((o) => (
                <Link
                  className="event"
                  href={"/opportunities/" + o.id}
                  key={o.id}
                >
                  <div className={"poster " + o.kind.toLowerCase()}>
                    <span>{o.organization_name}</span>
                    <strong>{o.title}</strong>
                    <small>{o.kind.replaceAll("_", " ").toLowerCase()}</small>
                  </div>
                  <div className="event-body">
                    <span className="mode">Apply externally</span>
                    <h3>{o.title}</h3>
                    <p>
                      {o.location} · {o.work_mode.toLowerCase()}
                    </p>
                    <div className="event-bottom">
                      {o.registration_closes_at ? (
                        <time dateTime={o.registration_closes_at}>
                          Closes{" "}
                          {new Date(
                            o.registration_closes_at,
                          ).toLocaleDateString("en-GB", {
                            day: "numeric",
                            month: "short",
                            timeZone: "UTC",
                          })}{" "}
                          · UTC
                        </time>
                      ) : (
                        <span>Deadline not provided</span>
                      )}
                      <span>View ↗</span>
                    </div>
                    {o.source_name && <small>Source: {o.source_name}</small>}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty">
              <h3>
                {search || kind
                  ? "No opportunities match yet."
                  : "Your next chapter is on its way."}
              </h3>
              <p>
                {search || kind
                  ? "Try another keyword or category."
                  : "No published opportunities are available yet. Check back as sources refresh."}
              </p>
              {(search || kind) && (
                <button
                  onClick={() => {
                    setKind("");
                    setSearch("");
                    setQuery("");
                  }}
                >
                  Clear filters
                </button>
              )}
            </div>
          )}
          <div className="pagination">
            {cursor > 0 && (
              <button
                disabled={loading}
                onClick={() => setCursor(Math.max(0, cursor - 12))}
              >
                Previous
              </button>
            )}
            {next !== null && (
              <button disabled={loading} onClick={() => setCursor(next)}>
                Next opportunities
              </button>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
