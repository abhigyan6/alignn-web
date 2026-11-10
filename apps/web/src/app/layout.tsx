import { AuthProvider, AccountControl } from "@/components/auth-provider";
import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
export const metadata: Metadata = {
  title: "Alignn · Find your next opportunity",
  description:
    "Discover opportunities, understand eligibility and keep your next steps together.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  const configured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
  const content = (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="site-header">
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
        {configured ? (
          <AccountControl />
        ) : (
          <Link className="button secondary" href="/login">
            Sign in
          </Link>
        )}
      </header>
      {children}
      <footer className="site-footer">
        <strong>Find your people. Find your next step.</strong>
        <span>Alignn · Opportunities with a clearer path forward.</span>
      </footer>
    </>
  );
  return (
    <html lang="en">
      <body>
        {configured ? <AuthProvider>{content}</AuthProvider> : content}
      </body>
    </html>
  );
}
