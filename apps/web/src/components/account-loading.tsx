import BrandLoader from "@/components/brand-loader";
import styles from "@/components/loading.module.css";
export default function AccountLoading({
  onboarding = false,
}: {
  onboarding?: boolean;
}) {
  return (
    <main
      id="main"
      className={`account-skeleton ${styles.account}`}
      aria-busy="true"
    >
      <div className={styles.accountHeading} role="status">
        <BrandLoader />
        <div>
          <h1>
            {onboarding ? "Loading your profile…" : "Loading your workspace…"}
          </h1>
          <p>Your information will appear here when it is ready.</p>
        </div>
      </div>
      <div className={styles.panel} aria-hidden="true">
        <span className={`${styles.shape} ${styles.panelTitle}`} />
        <div className={styles.fields}>
          {Array.from({ length: 4 }, (_, index) => (
            <div className={styles.field} key={index}>
              <span className={styles.shape} />
              <span className={styles.shape} />
            </div>
          ))}
        </div>
        <span className={`${styles.shape} ${styles.action}`} />
      </div>
    </main>
  );
}
