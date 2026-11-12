import styles from "@/components/loading.module.css";
export default function BrandLoader() {
  return (
    <span className={styles.brand} aria-hidden="true" data-ui="brand-loader">
      <svg viewBox="0 0 48 48" className={styles.mark}>
        <path
          d="M12 12C19-2 38 9 32 22L13 37C0 42 1 20 17 20H31C49 20 47 47 30 42M31 10V34"
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          strokeLinecap="round"
        />
      </svg>
      <svg viewBox="0 0 52 52" className={styles.indicator}>
        <circle cx="26" cy="26" r="24" />
      </svg>
    </span>
  );
}
