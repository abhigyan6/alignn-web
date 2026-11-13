import { AuthProvider, SessionBridge } from "@/components/auth-provider";
import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import CookieNotice from "@/components/cookie-notice";
import AppNavigation from "@/components/app-navigation";
import { BrandMark } from "@/components/icon";
import { isClerkPublishableKeyConfigured } from "@/lib/config";
export const metadata: Metadata = {
  title: "Alignn · Find your next opportunity",
  description:
    "Discover Indian internships, hackathons and events. Build a student profile, save opportunities and track your next steps with Alignn.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  const content = (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <Link className="brand" href="/">
          <BrandMark />
          alignn
        </Link>
        <AppNavigation authenticated={isClerkPublishableKeyConfigured} />
      </header>
      {isClerkPublishableKeyConfigured ? (
        <SessionBridge>{children}</SessionBridge>
      ) : (
        children
      )}
      <CookieNotice />
      <footer className="site-footer">
        <Link className="footer-brand" href="/">
          alignn<span>Find your next opportunity.</span>
        </Link>
        <p>Built for students. Connected to the original source.</p>
        <nav
          aria-label="Support and policies"
          style={{ display: "flex", flexWrap: "wrap", gap: "12px 20px" }}
        >
          <Link href="/privacy">Privacy</Link>
          <Link href="/terms">Terms</Link>
          <Link href="/cookies">Cookies</Link>
          <a href="mailto:contact@onlyward.app">Contact</a>
        </nav>
      </footer>
    </>
  );
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        {isClerkPublishableKeyConfigured ? (
          <AuthProvider>{content}</AuthProvider>
        ) : (
          content
        )}
      </body>
    </html>
  );
}
