import Link from "next/link";
import styles from "./legal.module.css";

export default function LegalPage({
  title,
  intro,
  sections,
}: {
  title: string;
  intro: string;
  sections: { title: string; text: string }[];
}) {
  return (
    <main id="main" className={styles.page}>
      <Link href="/explore">← Back to opportunities</Link>
      <header>
        <p className={styles.eyebrow}>
          Trust & information · Updated 12 November 2026
        </p>
        <h1>{title}</h1>
        <p>{intro}</p>
      </header>
      <p className={styles.notice}>
        Pre-launch draft. These pages describe the current product. Operator
        identity, retention periods and launch arrangements are being finalized.
      </p>
      <nav className={styles.links} aria-label="Policy pages">
        <Link href="/privacy">Privacy policy</Link>
        <Link href="/terms">Terms & conditions</Link>
        <Link href="/cookies">Cookie information</Link>
      </nav>
      {sections.map((section) => (
        <section key={section.title}>
          <h2>{section.title}</h2>
          <p>{section.text}</p>
        </section>
      ))}
      <section>
        <h2>Contact us</h2>
        <p>
          For questions, corrections or privacy requests, email the Alignn team
          at <a href="mailto:contact@onlyward.app">contact@onlyward.app</a>.
          Please do not send passwords, authentication codes or identity
          documents by email.
        </p>
      </section>
    </main>
  );
}
