import styles from "@/components/loading.module.css";
export default function OpportunitySkeleton() {
  return (
    <div role="status" aria-busy="true" className="opportunity-loading">
      <span className="sr-only">Loading opportunities…</span>
      <div className="event-grid" aria-hidden="true">
        {Array.from({ length: 4 }, (_, index) => (
          <div className={`event skeleton-card ${styles.card}`} key={index}>
            <div className={styles.cardTop}>
              <span
                className={`${styles.shape} ${styles.logo}`}
                data-skeleton-part="logo"
              />
              <span
                className={`${styles.shape} ${styles.category}`}
                data-skeleton-part="category"
              />
            </div>
            <div className={styles.title} data-skeleton-part="title">
              <span className={`${styles.shape} ${styles.titleLine}`} />
              <span className={`${styles.shape} ${styles.titleLine}`} />
            </div>
            <div className={styles.metadata} data-skeleton-part="metadata">
              <span className={styles.shape} />
              <span className={styles.shape} />
            </div>
            <div className={styles.skills} data-skeleton-part="skills">
              <span className={styles.shape} />
              <span className={styles.shape} />
            </div>
            <div className={styles.cardFooter} data-skeleton-part="footer">
              <span className={styles.shape} />
              <span className={styles.shape} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
