import OpportunitySkeleton from "@/components/opportunity-skeleton";
import styles from "@/components/loading.module.css";
export default function DiscoveryLoading() {
  return (
    <main id="main" className={`discovery-skeleton ${styles.discovery}`}>
      <div className={styles.discoveryHeading}>
        <h1>Find your next opportunity.</h1>
        <p>Internships, hackathons and events, brought together.</p>
        <div aria-hidden="true">
          <span className={`${styles.shape} ${styles.search}`} />
          <div className={styles.categories}>
            {Array.from({ length: 5 }, (_, index) => (
              <span className={styles.shape} key={index} />
            ))}
          </div>
        </div>
      </div>
      <OpportunitySkeleton />
    </main>
  );
}
