"use client";
import Link from "next/link";
import { Suspense, useEffect, useRef, useState, type FormEvent } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import OpportunityCard, { categoryIcons } from "@/components/opportunity-card";
import OpportunitySkeleton from "@/components/opportunity-skeleton";
import DiscoveryLoading from "@/components/discovery-loading";
import Icon, { type IconName } from "@/components/icon";
import { api, Opportunity } from "@/lib/api";
import { useSessionKey } from "@/lib/session-readiness";
import { useSavedIds } from "@/lib/saved-ids";
import SavedStatusNote from "@/components/saved-status-note";

const categories = [
  { value: "", label: "Everything", icon: "grid" },
  { value: "INTERNSHIP", label: "Internships", icon: "briefcase" },
  { value: "HACKATHON", label: "Hackathons", icon: "code" },
  { value: "WORKSHOP", label: "Workshops", icon: "calendar" },
  { value: "JOB", label: "Jobs", icon: "briefcase" },
  { value: "COMPETITION", label: "Competitions", icon: "spark" },
];
function Explore() {
  const params = useSearchParams(),
    router = useRouter();
  const initialKind = params.get("kind") ?? "";
  const [kind, setKind] = useState(
      categories.some((c) => c.value === initialKind) ? initialKind : "",
    ),
    [query, setQuery] = useState(params.get("q") ?? ""),
    [search, setSearch] = useState(params.get("q") ?? ""),
    [sort, setSort] = useState("match");
  const [items, setItems] = useState<Opportunity[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [rank, setRank] = useState(""),
    [next, setNext] = useState<number | null>(null),
    [cursor, setCursor] = useState(0),
    [attempt, setAttempt] = useState(0),
    [polls, setPolls] = useState(0);
  const sessionKey = useSessionKey();
  const sessionReady = sessionKey !== null;
  const saved = useSavedIds();
  const savedPending = saved.status !== "ready";
  // Best-fit ranking depends on who is signed in, so refresh it when the
  // session becomes ready or changes account. Other sorts are not personalized.
  const rankingSession = sort === "match" ? sessionKey : null;
  const loadedKey = useRef("");
  useEffect(() => {
    const nextKind = params.get("kind") ?? "",
      nextSearch = params.get("q") ?? "";
    setKind(categories.some((c) => c.value === nextKind) ? nextKind : "");
    setSearch(nextSearch);
    setQuery(nextSearch);
    setCursor(0);
  }, [params]);
  useEffect(() => setPolls(0), [kind, search, sort]);
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
    const key = [kind, search, sort, cursor].join("|");
    if (loadedKey.current !== key) {
      setItems([]);
      setNext(null);
      setRank("");
    }
    setLoading(true);
    setError("");
    const options = new URLSearchParams({
      q: search,
      sort,
      cursor: String(cursor),
      limit: "12",
    });
    if (kind) options.set("kind", kind);
    api<{
      items: Opportunity[];
      ranking_status: string;
      next_cursor: number | null;
    }>("/opportunities?" + options, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) {
          setItems(data.items);
          setRank(data.ranking_status);
          setNext(data.next_cursor);
          loadedKey.current = key;
        }
      })
      .catch((e) => {
        if (!controller.signal.aborted) {
          setError(e.message);
          setNext(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [kind, search, sort, cursor, attempt, rankingSession]);
  function navigate(nextKind: string, nextSearch: string) {
    const values = new URLSearchParams();
    if (nextKind) values.set("kind", nextKind);
    if (nextSearch) values.set("q", nextSearch);
    setKind(nextKind);
    setSearch(nextSearch);
    setCursor(0);
    router.replace(`/explore${values.size ? "?" + values : ""}`, {
      scroll: false,
    });
  }
  function submit(e: FormEvent) {
    e.preventDefault();
    navigate(kind, query.trim());
  }
  const currentCategory = categories.find((c) => c.value === kind);
  return (
    <main id="main" className="discovery-page">
      <div className="page-heading discovery-heading">
        <div>
          <div className="page-context">
            <span className="context-rule" />
            Made for your next step
          </div>
          <h1>Find your next opportunity.</h1>
          <p>Internships, hackathons and events, brought together.</p>
        </div>
        <Link className="profile-invitation" href="/onboarding?edit=1">
          <span className="profile-invitation-icon">
            <Icon name="user" size={23} />
          </span>
          <span>
            <strong>Make this feed yours</strong>
            <span>Add your skills and interests</span>
          </span>
          <Icon name="arrow" size={18} />
        </Link>
      </div>
      <form role="search" className="search discovery-search" onSubmit={submit}>
        <Icon name="search" size={22} />
        <label className="sr-only" htmlFor="search">
          Search opportunities
        </label>
        <input
          id="search"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Try a skill, role or opportunity"
        />
        <button className="button" type="submit">
          Search<span className="search-button-label"> opportunities</span>
          <Icon name="arrow" size={17} />
        </button>
      </form>
      <div
        className="category-bar"
        role="group"
        aria-label="Opportunity categories"
      >
        {categories.map((c) => (
          <button
            key={c.label}
            className={`category-control ${c.value.toLowerCase()}`}
            aria-pressed={kind === c.value}
            onClick={() => navigate(c.value, search)}
          >
            <span className="category-control-icon">
              <Icon
                name={(categoryIcons[c.value] ?? c.icon) as IconName}
                size={19}
              />
            </span>
            {c.label}
          </button>
        ))}
      </div>
      <section className="results" aria-labelledby="results-title">
        <div className="section-heading results-heading">
          <div>
            <h2 id="results-title">
              {search
                ? `Results for “${search}”`
                : kind
                  ? currentCategory?.label
                  : "Explore opportunities"}
            </h2>
            <p>
              {rank === "FRESH"
                ? "Ordered using your confirmed profile and preferences."
                : "Find something worth your next step."}
            </p>
          </div>
          <label className="sort-control">
            <span>Sort by</span>
            <select
              value={sort}
              onChange={(e) => {
                setCursor(0);
                setSort(e.target.value);
              }}
            >
              <option value="match">Best fit</option>
              <option value="deadline">Closing soon</option>
              <option value="newest">Newest first</option>
            </select>
          </label>
        </div>
        {saved.status === "unknown" && (
          <SavedStatusNote onRetry={saved.retry} />
        )}
        {rank === "SIGN_IN_REQUIRED" && sessionReady && (
          <div className="feed-note">
            <Icon name="user" size={17} />
            <p>
              <Link href="/login">
                Sign in for personalized recommendations.
              </Link>{" "}
              You’re browsing the newest opportunities.
            </p>
          </div>
        )}
        {rank === "PENDING" && polls < 6 && (
          <div className="feed-note" role="status">
            <Icon name="refresh" size={17} />
            <p>
              Your match ranking is being calculated. Showing newest
              opportunities for now.
            </p>
          </div>
        )}
        {(rank === "UNAVAILABLE" || (rank === "PENDING" && polls >= 6)) && (
          <div className="feed-note" role="status">
            <Icon name="refresh" size={17} />
            <p>
              Matching is taking longer than expected. You can keep browsing.
            </p>
            <button
              className="text-button"
              onClick={() => {
                setPolls(0);
                setAttempt((v) => v + 1);
              }}
            >
              Check ranking again
            </button>
          </div>
        )}
        {(search || kind) && (
          <div className="active-filters">
            <span>
              {[currentCategory?.value ? currentCategory.label : null, search]
                .filter(Boolean)
                .join(" / ")}
            </span>
            <button
              className="text-button"
              onClick={() => {
                setQuery("");
                navigate("", "");
              }}
            >
              <Icon name="close" size={15} />
              Clear filters
            </button>
          </div>
        )}
        {error && (
          <div className="feedback error-feedback" role="alert">
            <div>
              <strong>Unable to load opportunities.</strong>
              <p>{error}</p>
            </div>
            <button
              className="button secondary"
              onClick={() => setAttempt((v) => v + 1)}
            >
              Try again
            </button>
          </div>
        )}
        {loading && items.length === 0 ? (
          <OpportunitySkeleton />
        ) : items.length > 0 ? (
          <>
            <div className="refresh-status" role="status">
              {loading ? "Updating opportunities…" : ""}
            </div>
            <div className="event-grid">
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
        ) : !error ? (
          <div className="empty discovery-empty">
            <span className="empty-icon">
              <Icon name="search" size={30} />
            </span>
            <h3>
              {search || kind
                ? "No opportunities match these filters."
                : "The next opportunities will appear here."}
            </h3>
            <p>
              {search || kind
                ? "Try a broader keyword or explore another category."
                : "There are no active listings to show right now. Try again after sources refresh."}
            </p>
            <button
              className="button secondary"
              onClick={() => {
                if (search || kind) {
                  setQuery("");
                  navigate("", "");
                } else setAttempt((v) => v + 1);
              }}
            >
              {search || kind
                ? "Explore all opportunities"
                : "Refresh opportunities"}
            </button>
          </div>
        ) : null}
        <div className="pagination">
          <span>
            {items.length > 0 ? `Page ${Math.floor(cursor / 12) + 1}` : ""}
          </span>
          <div>
            {cursor > 0 && (
              <button
                disabled={loading || Boolean(error)}
                onClick={() => {
                  setCursor(Math.max(0, cursor - 12));
                  document
                    .getElementById("results-title")
                    ?.scrollIntoView({ block: "start" });
                }}
              >
                Previous
              </button>
            )}
            {next !== null && (
              <button
                className="button secondary"
                disabled={loading || Boolean(error)}
                onClick={() => {
                  setCursor(next);
                  document
                    .getElementById("results-title")
                    ?.scrollIntoView({ block: "start" });
                }}
              >
                Next opportunities
                <Icon name="arrow" size={16} />
              </button>
            )}
          </div>
        </div>
      </section>
      <div className="source-note">
        <Icon name="external" size={16} />
        <p>
          Explore here. Apply on the original website. Check its current
          requirements and availability before applying.
        </p>
      </div>
    </main>
  );
}
export default function ExplorePage() {
  return (
    <Suspense fallback={<DiscoveryLoading />}>
      <Explore />
    </Suspense>
  );
}
