import Link from "next/link";
import type { ReactNode } from "react";

export const authAppearance = {
  variables: {
    colorPrimary: "#123e2f",
    colorBackground: "#f4f2e9",
    borderRadius: "12px",
    fontFamily: "Manrope, sans-serif",
  },
  elements: {
    rootBox: "auth-clerk-root",
    cardBox: "auth-clerk-box",
    card: "auth-clerk-card",
    footer: "auth-clerk-footer",
    headerTitle: "auth-clerk-title",
    headerSubtitle: "auth-clerk-subtitle",
    socialButtonsBlockButton: "auth-clerk-social",
    formButtonPrimary: "auth-clerk-primary",
    formFieldInput: "auth-clerk-input",
    footerActionLink: "auth-clerk-link",
    identityPreviewEditButton: "auth-clerk-link",
  },
};

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
    <main id="main" className="auth auth-page">
      <section className="auth-shell" aria-labelledby="auth-title">
        <div className="auth-story">
          <Link className="auth-mark" href="/explore" aria-label="Alignn home">
            <svg aria-hidden="true" viewBox="0 0 48 48">
              <path
                d="M12 12C19-2 38 9 32 22L13 37C0 42 1 20 17 20H31C49 20 47 47 30 42M31 10V34"
                fill="none"
                stroke="currentColor"
                strokeWidth="5"
                strokeLinecap="round"
              />
            </svg>
            <span>alignn</span>
          </Link>
          <div className="auth-story-copy">
            <h1 id="auth-title">{title}</h1>
            <p>{description}</p>
          </div>
          <div className="auth-signal" aria-hidden="true">
            <span>Discover</span>
            <span>Align</span>
            <span>Move forward</span>
          </div>
        </div>
        <div className="auth-panel">
          {children}
          <Link className="auth-ghost-link" href="/explore">
            Continue browsing first
          </Link>
        </div>
      </section>
    </main>
  );
}
