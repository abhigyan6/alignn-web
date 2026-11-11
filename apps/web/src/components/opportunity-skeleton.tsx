export default function OpportunitySkeleton() {
  return (
    <div role="status" aria-busy="true" className="opportunity-loading">
      <span className="sr-only">Finding opportunities…</span>
      <div className="event-grid" aria-hidden="true">
        {Array.from({ length: 4 }, (_, index) => (
          <div className="event skeleton-card" key={index}>
            <div className="poster skeleton-poster">
              <span className="skeleton skeleton-label" />
              <span className="skeleton skeleton-heading" />
              <span className="skeleton skeleton-heading short" />
              <span className="skeleton skeleton-label" />
            </div>
            <div className="event-body skeleton-card-body">
              <span className="skeleton skeleton-label" />
              <span className="skeleton skeleton-line" />
              <span className="skeleton skeleton-line short" />
              <div className="event-bottom">
                <span className="skeleton skeleton-label" />
                <span className="skeleton skeleton-icon" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
