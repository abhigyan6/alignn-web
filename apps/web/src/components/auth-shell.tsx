import Link from "next/link";
import type { ReactNode } from "react";
import styles from "./auth-shell.module.css";

export const authAppearance = {
  variables: {
    // Clerk derives its own --accent variable. Referring to that name creates a cycle.
    colorPrimary: "#145640",
    colorPrimaryForeground: "#ffffff",
    colorBackground: "#ffffff",
    colorForeground: "#182821",
    colorInput: "#ffffff",
    colorInputForeground: "#182821",
    borderRadius: "10px",
    fontFamily: "Manrope, Arial, sans-serif",
  },
  elements: {
    rootBox: `${styles.clerkRoot} auth-clerk-root`,
    cardBox: styles.clerkBox,
    card: styles.clerkCard,
    footer: styles.clerkFooter,
    headerTitle: styles.clerkTitle,
    headerSubtitle: styles.clerkSubtitle,
    socialButtonsBlockButton: styles.clerkSocial,
    formButtonPrimary: styles.clerkPrimary,
    formFieldInput: styles.clerkInput,
    footerActionLink: styles.clerkLink,
    identityPreviewEditButton: styles.clerkLink,
  },
};

function JourneyIcon({ kind }: { kind: "profile" | "match" | "save" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      {kind === "profile" ? (
        <>
          <rect x="3.5" y="4.5" width="17" height="15" rx="3" />
          <circle cx="9" cy="10" r="2" />
          <path d="M6 16c.5-2.5 5.5-2.5 6 0m3-7h3m-3 4h3" />
        </>
      ) : kind === "match" ? (
        <>
          <path d="M4 6h16M4 12h16M4 18h16" />
          <circle cx="9" cy="6" r="2" />
          <circle cx="16" cy="12" r="2" />
          <circle cx="8" cy="18" r="2" />
        </>
      ) : (
        <path d="M7 4h10a1 1 0 0 1 1 1v15l-6-4-6 4V5a1 1 0 0 1 1-1Z" />
      )}
    </svg>
  );
}

export default function AuthShell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <main id="main" className={styles.page}>
      <div className={`${styles.shell} auth-shell`}>
        <section className={styles.story} aria-labelledby="auth-title">
          <div>
            <h1 id="auth-title">{title}</h1>
            <p className={styles.description}>{description}</p>
          </div>
          <ol className={styles.journey} aria-label="How Alignn works">
            <li>
              <span className={styles.journeyIcon}>
                <JourneyIcon kind="profile" />
              </span>
              <div>
                <strong>Start with you</strong>
                <p>Add your education, skills and interests.</p>
              </div>
            </li>
            <li>
              <span className={styles.journeyIcon}>
                <JourneyIcon kind="match" />
              </span>
              <div>
                <strong>Find a better fit</strong>
                <p>Explore Indian internships, hackathons and events.</p>
              </div>
            </li>
            <li>
              <span className={styles.journeyIcon}>
                <JourneyIcon kind="save" />
              </span>
              <div>
                <strong>Keep your next steps together</strong>
                <p>Save opportunities and track your applications.</p>
              </div>
            </li>
          </ol>
          <p className={styles.sourceNote}>
            You apply on the original platform. Your shortlist stays here.
          </p>
        </section>
        <section
          className={`${styles.panel} auth-panel`}
          aria-label="Account access"
        >
          <div className={styles.formSlot}>{children}</div>
          <Link className={styles.browseLink} href="/explore">
            Continue browsing first
          </Link>
        </section>
      </div>
    </main>
  );
}
