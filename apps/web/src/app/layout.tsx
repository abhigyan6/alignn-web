import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
export const metadata: Metadata = {
  title: "Alignn · Find your next opportunity",
  description:
    "Discover opportunities, understand eligibility and keep your next steps together.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip" href="#main">
          Skip to content
        </a>
        <header>
          <Link className="brand" href="/explore">
            <svg aria-hidden="true" viewBox="0 0 48 48">
              <path
                d="M12 12C19-2 38 9 32 22L13 37C0 42 1 20 17 20H31C49 20 47 47 30 42M31 10V34"
                fill="none"
                stroke="currentColor"
                strokeWidth="5"
                strokeLinecap="round"
              />
            </svg>
            alignn
          </Link>
          <nav aria-label="Main navigation">
            <Link href="/explore">Explore</Link>
            <Link href="/workspace">My workspace</Link>
          </nav>
          <Link className="button secondary" href="/login">
            Sign in
          </Link>
        </header>
        {children}
        <footer>
          <strong>Find your people. Find your next step.</strong>
          <span>Alignn · Opportunities with a clearer path forward.</span>
        </footer>
      </body>
    </html>
  );
}
