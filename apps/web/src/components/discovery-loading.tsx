import OpportunitySkeleton from "@/components/opportunity-skeleton";
export default function DiscoveryLoading() {
  return (
    <main id="main" className="discovery-skeleton">
      <div className="discovery-skeleton-heading" aria-hidden="true">
        <span className="skeleton skeleton-heading" />
        <span className="skeleton skeleton-line short" />
        <span className="skeleton skeleton-field" />
      </div>
      <OpportunitySkeleton />
    </main>
  );
}
