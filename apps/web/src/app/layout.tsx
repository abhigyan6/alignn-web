import { AuthProvider, SessionBridge } from "@/components/auth-provider";
import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import AppNavigation from "@/components/app-navigation";
import SiteIntro, { introScript } from "@/components/site-intro";
export const metadata: Metadata = {
  title: "Alignn · Find your next opportunity",
  description: "Alignn is building a clearer path to your next opportunity.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  const configured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
  const content = (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <Link className="brand" href="/">
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
        <AppNavigation authenticated={configured} />
      </header>
      {configured ? <SessionBridge>{children}</SessionBridge> : children}
      <footer className="site-footer">
        <strong>Find your people. Find your next step.</strong>
        <span>Discover. Save. Take your next step.</span>
      </footer>
    </>
  );
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <script dangerouslySetInnerHTML={{ __html: introScript }} />
        <SiteIntro />
        {configured ? <AuthProvider>{content}</AuthProvider> : content}
      </body>
    </html>
  );
}
