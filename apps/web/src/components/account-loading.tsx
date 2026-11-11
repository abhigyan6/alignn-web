import BrandLoader from "@/components/brand-loader";
export default function AccountLoading({
  onboarding = false,
}: {
  onboarding?: boolean;
}) {
  return (
    <main
      id="main"
      className={`account-skeleton ${onboarding ? "onboarding" : "workspace"}`}
      aria-busy="true"
    >
      <div className="account-loading-heading" role="status">
        <BrandLoader />
        <div>
          <p className="loading-eyebrow">A moment to align</p>
          <h1>
            {onboarding
              ? "Making room for your next chapter."
              : "Getting your account ready."}
          </h1>
        </div>
      </div>
      <div className="account-skeleton-content" aria-hidden="true">
        <span className="skeleton skeleton-heading" />
        <span className="skeleton skeleton-line short" />
        <div className="skeleton-fields">
          {Array.from({ length: 4 }, (_, index) => (
            <span className="skeleton skeleton-field" key={index} />
          ))}
        </div>
        <span className="skeleton skeleton-action" />
      </div>
    </main>
  );
}
